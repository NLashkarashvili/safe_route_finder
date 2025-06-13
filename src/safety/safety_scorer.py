"""
Safety scoring functionality.
"""
import datetime
from typing import Any, Dict, Tuple
import networkx as nx
from shapely.geometry import LineString
import geopandas as gpd


class SafetyScorer:
    def __init__(self, data_loader: Any):
        self.data_loader = data_loader
        self.current_time = datetime.datetime.now()
        # Cache for edge safety scores to avoid recalculation
        self.edge_safety_cache = {}

    def calculate_edge_safety(self, G: nx.MultiDiGraph, u: int, v: int, k: int,
                            data: Dict, safety_pois: gpd.GeoDataFrame) -> float:
        """Calculate safety score for a single edge."""
        # Check cache first
        cache_key = f"{u}_{v}_{k}"
        if cache_key in self.edge_safety_cache:
            return self.edge_safety_cache[cache_key]
        print("Graph CRS CODE IS", G.graph['crs'])
        # Start with a neutral base score
        base_score = 5.0
        
        # Road type safety (0-3 points)
        road_safety = self._get_road_safety_score(data.get('highway', ''))
        
        # Street lighting (0-2 points)
        lighting_safety = self._get_lighting_score(data.get('lit') == 'yes')
        
        # LSOA crime score (-10 to 0 points)
        edge_midpoint = self._get_edge_midpoint(G, u, v)
        crime_safety = self._get_crime_safety_score(edge_midpoint)
        
        # POI proximity (varies)
        poi_safety = 0
        if not safety_pois.empty and hasattr(safety_pois, 'sindex'):
            poi_safety = self._get_poi_safety_score(G, u, v, safety_pois)

        # Combine all factors
        safety_score = base_score + road_safety + lighting_safety + crime_safety + poi_safety
        
        # Ensure score is within bounds
        final_score = max(0, min(10, safety_score))
        
        # Cache the result
        self.edge_safety_cache[cache_key] = final_score
        
        return final_score

    def _get_road_safety_score(self, highway: str) -> float:
        """Calculate safety score based on road type."""
        if isinstance(highway, list):
            highway = highway[0] if highway else ''

        road_scores = {
            'footway': 3,
            'pedestrian': 3,
            'path': 3,
            'residential': 1,
            'living_street': 1,
            'primary': -1,
            'secondary': -1,
            'tertiary': -1,
            'motorway': -3,
            'trunk': -3
        }
        return road_scores.get(highway, 0)

    def _get_lighting_score(self, is_lit: bool) -> float:
        """Calculate safety score based on street lighting."""
        is_night = self.current_time.hour >= 20 or self.current_time.hour < 8
        if is_lit:
            return 2 if is_night else 0.5
        return -2 if is_night else 0

    def _get_edge_midpoint(self, G: nx.MultiDiGraph, u: int, v: int) -> Tuple[float, float]:
        """Calculate the midpoint of an edge."""
        return (
            (G.nodes[u]['y'] + G.nodes[v]['y']) / 2,
            (G.nodes[u]['x'] + G.nodes[v]['x']) / 2
        )

    def _get_crime_safety_score(self, point: Tuple[float, float]) -> float:
        """Calculate safety score based on crime data."""
        # point is (y, x) but get_lsoa_for_coordinate expects (x, y)
        # Swap the order of coordinates
        y, x = point
        lsoa = self.data_loader.get_lsoa_for_coordinate(x, y)
        
        # Get the safety scores for this LSOA
        lsoa_scores = self.data_loader.load_lsoa_crime_data().get(lsoa, {'routing_score': 5})
        
        # Use the routing_score directly (0-10 where higher means more dangerous)
        # Negate it so higher crime = lower safety
        routing_score = lsoa_scores.get('routing_score', 5)
        safety_modifier = -routing_score
        
        # Debug output
        print(f"LSOA: {lsoa}, Routing Score: {routing_score}, Safety Modifier: {safety_modifier}")
        
        return safety_modifier

    def _get_poi_safety_score(self, G: nx.MultiDiGraph, u: int, v: int,
                            safety_pois: gpd.GeoDataFrame) -> float:
        """Calculate safety score based on nearby POIs."""
        # Create a unique key for this edge
        edge_key = f"{u}_{v}"
        
        # Check if we've already processed this edge with a different key
        alt_edge_key = f"{v}_{u}"  # Edges can be bidirectional
        
        # Use a class-level cache for POI calculations
        if not hasattr(self, 'poi_cache'):
            self.poi_cache = {}
            
        # Check cache
        if edge_key in self.poi_cache:
            return self.poi_cache[edge_key]
        if alt_edge_key in self.poi_cache:
            return self.poi_cache[alt_edge_key]
        
        # If not in cache, calculate
        edge_line = LineString([
            (G.nodes[u]['x'], G.nodes[u]['y']),
            (G.nodes[v]['x'], G.nodes[v]['y'])
        ])
        edge_gdf = gpd.GeoDataFrame(geometry=[edge_line], crs="EPSG:4326")
        
        # Convert to a projected CRS for accurate buffer calculation
        # Using British National Grid for UK locations
        edge_gdf_projected = edge_gdf.to_crs("EPSG:27700")
        
        # Buffer in meters (30 meters)
        buffer_dist = 30
        edge_buffer = edge_gdf_projected.buffer(buffer_dist).iloc[0]
        
        # Convert buffer back to WGS84 for intersection with POIs
        edge_buffer_wgs84 = gpd.GeoDataFrame(geometry=[edge_buffer], crs="EPSG:27700").to_crs("EPSG:4326").geometry.iloc[0]

        # Ensure safety_pois has the right CRS
        if safety_pois.crs != "EPSG:4326":
            safety_pois = safety_pois.to_crs("EPSG:4326")

        possible_matches_index = list(safety_pois.sindex.intersection(edge_buffer_wgs84.bounds))
        possible_matches = safety_pois.iloc[possible_matches_index]
        precise_matches = possible_matches[possible_matches.intersects(edge_buffer_wgs84)]

        safety_score = 0
        for _, poi in precise_matches.iterrows():
            safety_score += self._calculate_poi_modifier(poi)
            
        # Cache the result
        self.poi_cache[edge_key] = safety_score
        
        return safety_score

    def _calculate_poi_modifier(self, poi: gpd.GeoSeries) -> float:
        """Calculate safety modifier for a single POI."""
        hour = self.current_time.hour
        
        if 'amenity' in poi and poi['amenity'] is not None:
            if poi['amenity'] in ['police', 'hospital', 'pharmacy']:
                return 2
            elif poi['amenity'] in ['bar', 'pub', 'casino', 'nightclub']:
                return -2 if (hour >= 22 or hour < 6) else 0
            elif poi['amenity'] in ['theatre', 'cinema', 'arts_centre']:
                return 0.5

        elif 'leisure' in poi and poi['leisure'] is not None:
            if poi['leisure'] in ['park', 'garden', 'nature_reserve']:
                return 1 if (8 <= hour < 20) else -2

        elif 'public_transport' in poi and poi['public_transport'] is not None:
            return 1 if (6 <= hour < 22) else -1

        return 0
