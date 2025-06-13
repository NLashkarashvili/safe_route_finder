"""
Data loading functionality for the safe route finder.
"""
import os
import geopandas as gpd
import osmnx as ox
import pandas as pd
from shapely.geometry import Point
from pyproj import CRS
import networkx as nx


class DataLoader:
    """
    Class for loading various data needed for the safe route finder.
    """
    
    def __init__(self):
        """Initialize the data loader."""
        self.lsoa_gdf = None
        self.lsoa_crime_data = None
        
    def load_safety_pois(self, center_point, dist=800):
        """
        Load Points of Interest (POIs) that are relevant for safety calculations.
        
        Args:
            center_point: Tuple of (lat, lon) for the center point
            dist: Distance in meters to search for POIs
            
        Returns:
            GeoDataFrame containing POIs with safety relevance
        """
        print(f"Loading safety POIs around {center_point} with distance {dist}m")
        
        try:
            # Since OSMnx POI loading is not working, create mock POI data
            print("Creating mock POI data for visualization...")
            
            # Convert distance from meters to degrees (approximate)
            # 1 degree latitude is about 111 km, 1 degree longitude varies but around 111km at equator
            dist_deg = dist / 111000  # Convert meters to approximate degrees
            
            # Create a grid of points around the center
            lat, lon = center_point
            
            # Create mock POI data
            poi_data = []
            
            # Add some police stations
            poi_data.append({
                'geometry': Point(lon - 0.5 * dist_deg, lat + 0.3 * dist_deg),
                'amenity': 'police',
                'name': 'Police Station North',
                'safety_type': 'positive'
            })
            
            poi_data.append({
                'geometry': Point(lon + 0.4 * dist_deg, lat - 0.2 * dist_deg),
                'amenity': 'police',
                'name': 'Police Station South',
                'safety_type': 'positive'
            })
            
            # Add some hospitals
            poi_data.append({
                'geometry': Point(lon - 0.3 * dist_deg, lat - 0.4 * dist_deg),
                'amenity': 'hospital',
                'name': 'General Hospital',
                'safety_type': 'positive'
            })
            
            # Add some bars/pubs
            poi_data.append({
                'geometry': Point(lon + 0.2 * dist_deg, lat + 0.2 * dist_deg),
                'amenity': 'bar',
                'name': 'The Local Pub',
                'safety_type': 'negative'
            })
            
            poi_data.append({
                'geometry': Point(lon - 0.1 * dist_deg, lat + 0.4 * dist_deg),
                'amenity': 'pub',
                'name': 'Crown & Anchor',
                'safety_type': 'negative'
            })
            
            poi_data.append({
                'geometry': Point(lon + 0.3 * dist_deg, lat - 0.3 * dist_deg),
                'amenity': 'nightclub',
                'name': 'Nightclub Zone',
                'safety_type': 'negative'
            })
            
            # Add some parks
            poi_data.append({
                'geometry': Point(lon - 0.2 * dist_deg, lat - 0.1 * dist_deg),
                'leisure': 'park',
                'name': 'Central Park',
                'safety_type': 'positive'
            })
            
            poi_data.append({
                'geometry': Point(lon + 0.1 * dist_deg, lat + 0.5 * dist_deg),
                'leisure': 'garden',
                'name': 'Botanical Gardens',
                'safety_type': 'positive'
            })
            
            # Add some transit stations
            poi_data.append({
                'geometry': Point(lon, lat),
                'public_transport': 'station',
                'name': 'Central Station',
                'safety_type': 'neutral'
            })
            
            poi_data.append({
                'geometry': Point(lon - 0.4 * dist_deg, lat + 0.1 * dist_deg),
                'public_transport': 'station',
                'name': 'North Station',
                'safety_type': 'neutral'
            })
            
            # Add some restaurants/cafes
            poi_data.append({
                'geometry': Point(lon + 0.15 * dist_deg, lat - 0.15 * dist_deg),
                'amenity': 'restaurant',
                'name': 'Fine Dining',
                'safety_type': 'neutral'
            })
            
            poi_data.append({
                'geometry': Point(lon - 0.25 * dist_deg, lat + 0.25 * dist_deg),
                'amenity': 'cafe',
                'name': 'Coffee Shop',
                'safety_type': 'neutral'
            })
            
            # Create GeoDataFrame
            safety_pois = gpd.GeoDataFrame(poi_data, crs="EPSG:4326")
            
            print(f"Created {len(safety_pois)} mock POIs")
            print(f"POI types: {safety_pois['safety_type'].value_counts().to_dict()}")
            
            return safety_pois
                
        except Exception as e:
            print(f"Error creating mock POIs: {e}")
            return gpd.GeoDataFrame()
    
    def load_crime_data(self, bounds=None):
        """
        Load crime data for the area of interest.
        
        Args:
            bounds: Bounding box for the area of interest
            
        Returns:
            GeoDataFrame containing crime data
        """
        return gpd.GeoDataFrame()
    
    def get_lsoa_for_coordinate(self, lon, lat):
        """
        Get the LSOA (Lower Super Output Area) code for a given coordinate.
        
        Args:
            lon: X coordinate 
            lat: Y coordinate
            
        Returns:
            String LSOA code
        """
        # Try to load and use the LSOA geojson file
        if self.lsoa_gdf is None:
            try:
                lsoa_file = "C:\\Users\\Nineli.Lashkarashvil\\SperryRail\\Innovation\\data_science\\CPD\\safe_route_finder\\lsoa_geojson_map.geojson"
                self.lsoa_gdf = gpd.read_file(lsoa_file)
                # Ensure LSOA data is in EPSG:4326
                if self.lsoa_gdf.crs != "EPSG:4326":
                    self.lsoa_gdf = self.lsoa_gdf.to_crs("EPSG:4326")
            except Exception as e:
                print(f"Error loading LSOA file: {e}")
                return None

        # Create point in the correct CRS
        point = gpd.points_from_xy([lon], [lat], crs=self.lsoa_gdf.crs)
        
        # Use spatial join for faster lookup (much more efficient than iterating)
        point_gdf = gpd.GeoDataFrame(geometry=point, crs=self.lsoa_gdf.crs)
        joined = gpd.sjoin(point_gdf, self.lsoa_gdf, how="left", predicate="within")
        
        if not joined.empty and 'LSOA11CD' in joined.columns and not joined['LSOA11CD'].isna().all():
            lsoa_code = joined['LSOA11CD'].iloc[0]
            return lsoa_code
            
        # If spatial join fails, fall back to iterating through polygons
        for _, row in self.lsoa_gdf.iterrows():
            if row.geometry.contains(point):
                lsoa_code = row['LSOA11CD']
                return lsoa_code

        # If we get here, no LSOA was found
        return None
        
    def load_lsoa_crime_data(self):
        """
        Load crime data aggregated by LSOA from CSV file.
        
        Returns:
            Dictionary mapping LSOA codes to crime statistics
        """
        if self.lsoa_crime_data is not None:
            return self.lsoa_crime_data
        
        csv_file = "C:\\Users\\Nineli.Lashkarashvil\\SperryRail\\Innovation\\data_science\\CPD\\safe_route_finder\\output_safety_scores.csv"
        crime_df = pd.read_csv(csv_file)
        
        lsoa_data = {}
        for _, row in crime_df.iterrows():
            # Use the correct column name from your CSV file
            lsoa_code = row['LSOA Code']  # Keep this as 'LSOA Code' if that's what's in your CSV
            lsoa_data[lsoa_code] = {'routing_score': row['routing_score']}
        
        self.lsoa_crime_data = lsoa_data
        return lsoa_data
        
    def load_network(self, center_point, dist=1000):
        """
        Load the street network around a center point.
        
        Args:
            center_point: Tuple of (lat, lon) for the center point
            dist: Distance in meters to include in the network
            
        Returns:
            NetworkX MultiDiGraph of the street network
        """
        # Configure OSMnx to use EPSG:4326 (WGS84)
        ox.settings.use_cache = True
        ox.settings.log_console = False
        
        # Download the street network
        G = ox.graph_from_point(center_point, dist=dist, network_type='walk')
        
        # Ensure the graph is using EPSG:4326
        if G.graph['crs'] != 'EPSG:4326':
            G = ox.project_graph(G, to_crs='EPSG:4326')
            print(f"Projected graph to EPSG:4326")
        
        print(f"Graph CRS: {G.graph['crs']}")
        
        return G
