"""
Route finding functionality.
"""
from typing import Any, Dict, List, Tuple
import networkx as nx
import osmnx as ox


class RouteFinder:
    def __init__(self, data_loader: Any, safety_scorer: Any):
        self.data_loader = data_loader
        self.safety_scorer = safety_scorer

    def find_routes(self, start_point: Tuple[float, float],
                   end_point: Tuple[float, float]) -> Dict[str, List[int]]:
        """Find both shortest and safest routes between two points."""
        # Load network and POIs
        G = self.data_loader.load_network(start_point)
        safety_pois = self.data_loader.load_safety_pois(start_point)

        # Add safety scores to the graph
        G = self._add_safety_scores(G, safety_pois)

        # Get nearest nodes
        start_node = ox.distance.nearest_nodes(G, start_point[1], start_point[0])
        end_node = ox.distance.nearest_nodes(G, end_point[1], end_point[0])

        # Calculate routes
        shortest_route = nx.shortest_path(G, start_node, end_node, weight='length')
        safest_route = nx.shortest_path(G, start_node, end_node, weight='safe_route')

        return {
            'shortest': shortest_route,
            'safest': safest_route
        }

    def _add_safety_scores(self, G: nx.MultiDiGraph, safety_pois: Any) -> nx.MultiDiGraph:
        """Add safety scores to the graph edges."""
        for u, v, k, data in G.edges(keys=True, data=True):
            # Calculate safety score
            safety_score = self.safety_scorer.calculate_edge_safety(G, u, v, k, data, safety_pois)
            
            # Store the safety score
            G[u][v][k]['safety_score'] = safety_score
            
            # Create composite weight for safe routing
            safety_factor = 10 - safety_score  # Invert so safer paths have lower values
            length = data['length']
            G[u][v][k]['safe_route'] = length * (1 + (safety_factor / 5))

        return G

    def analyze_route(self, G: nx.MultiDiGraph, route: List[int], route_type: str) -> Dict:
        """Analyze the safety characteristics of a route."""
        total_length = 0
        total_safety_score = 0
        segment_details = []

        # Analyze each segment of the route
        for i in range(len(route) - 1):
            u, v = route[i], route[i + 1]
            
            # Get edge data (use first edge if multiple exist)
            edge_data = G[u][v][0]
            
            length = edge_data['length']
            safety_score = edge_data['safety_score']
            
            total_length += length
            total_safety_score += safety_score * length  # Weight by segment length
            
            segment_details.append({
                'start_node': u,
                'end_node': v,
                'length': length,
                'safety_score': safety_score,
                'highway_type': edge_data.get('highway', 'unknown')
            })

        # Calculate average safety score weighted by segment length
        avg_safety_score = total_safety_score / total_length if total_length > 0 else 0

        return {
            'route_type': route_type,
            'total_length': total_length,
            'average_safety_score': avg_safety_score,
            'segment_details': segment_details
        }
