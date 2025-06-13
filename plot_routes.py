"""
Script to plot shortest and safest routes between two points
"""
import matplotlib
# Force matplotlib to use a non-interactive backend
matplotlib.use('Agg')

import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
import argparse
import time
import geopandas as gpd
from shapely.geometry import Point
import sys
import os

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
from src.data.data_loader import DataLoader
from src.safety.safety_scorer import SafetyScorer
from src.visualization.route_visualizer import RouteVisualizer

def plot_routes(start_lat: float, start_lon: float, end_lat: float, end_lon: float,
               radius: int = 800, output_file: str = None) -> None:
    """
    Plot the shortest and safest routes between two points.
    
    Args:
        start_lat: Starting point latitude
        start_lon: Starting point longitude
        end_lat: Ending point latitude
        end_lon: Ending point longitude
        radius: Network radius in meters
        output_file: Optional output file path for the map
    """
    start_time = time.time()
    
    # Calculate the center point between start and end
    center_lat = (start_lat + end_lat) / 2
    center_lon = (start_lon + end_lon) / 2
    
    # Calculate the distance between start and end points (in meters)
    # This is a rough calculation using the Haversine formula
    from math import radians, cos, sin, asin, sqrt
    def haversine(lon1, lat1, lon2, lat2):
        # Convert decimal degrees to radians
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        # Radius of earth in meters
        r = 6371000
        return c * r
    
    # Calculate the distance between points
    point_distance = haversine(start_lon, start_lat, end_lon, end_lat)
    
    # Make sure the radius is at least 1.5 times the distance between points
    # This ensures the network includes both points with some margin
    effective_radius = max(radius, point_distance * 1.5)
    
    # Load the street network around the center point
    print(f"Loading street network around center ({center_lat:.4f}, {center_lon:.4f}) with radius {effective_radius:.0f}m...")
    G = ox.graph_from_point((center_lat, center_lon), dist=effective_radius, network_type='walk')
    
    # Project the graph to use meters
    G = ox.project_graph(G)
    
    # Load safety POIs
    print("Loading safety POIs...")
    safety_pois = gpd.GeoDataFrame()
    try:
        # Get POIs like police stations, hospitals, etc.
        tags = {
            'amenity': ['police', 'hospital', 'clinic', 'pharmacy', 'bar', 'pub', 'nightclub'],
            'leisure': ['park', 'garden'],
            'public_transport': True
        }
        safety_pois = ox.geometries_from_point((start_lat, start_lon), tags, dist=radius)
        safety_pois = safety_pois.to_crs(G.graph['crs'])
        print(f"Loaded {len(safety_pois)} safety POIs")
    except Exception as e:
        print(f"Warning: Could not load safety POIs: {e}")
    
    # Initialize the safety scorer
    print("Initializing safety scorer...")
    data_loader = DataLoader()
    safety_scorer = SafetyScorer(data_loader)
    
    # Add safety scores to each edge in the graph
    print("Calculating safety scores for all edges...")
    edge_count = 0
    safety_scores = []
    
    for u, v, k, data in G.edges(keys=True, data=True):
        # Calculate safety score
        safety_score = safety_scorer.calculate_edge_safety(G, u, v, k, data, safety_pois)
        data['safety_score'] = safety_score
        safety_scores.append(safety_score)
        
        # Create a weight that properly prioritizes safety
        # For safe routing: lower safety = higher weight (cost)
        # This makes the algorithm avoid unsafe areas
        safety_weight = 10 - safety_score  # Invert the safety score (0-10 scale)
        
        # Combine safety and distance
        # Alpha controls the balance between safety and distance
        # Higher alpha = more emphasis on safety
        alpha = 0.8  # 80% safety, 20% distance
        
        # Normalize distance to be on a similar scale as safety
        # Typical road segment might be 50-200 meters
        normalized_distance = data['length'] / 100  # Scale to be roughly 0.5-2
        
        # Combined weight: alpha * safety_weight + (1-alpha) * normalized_distance
        data['safe_weight'] = (alpha * safety_weight) + ((1 - alpha) * normalized_distance)
        
        edge_count += 1
        if edge_count % 100 == 0:
            print(f"Processed {edge_count}/{len(G.edges)} edges...")
    
    # Calculate average safety score
    if safety_scores:
        avg_safety = sum(safety_scores) / len(safety_scores)
        print(f"Average safety score across all edges: {avg_safety:.2f}/10")
    else:
        print("Warning: No safety scores calculated!")
    
    # Find the nearest nodes to our start and end points
    start_node = ox.distance.nearest_nodes(G, start_lon, start_lat)
    end_node = ox.distance.nearest_nodes(G, end_lon, end_lat)
    
    # Check if the network is too small to contain both points
    try:
        # Calculate the shortest route (based only on distance)
        print("Calculating shortest route...")
        shortest_route = nx.shortest_path(G, start_node, end_node, weight='length')
        
        # Calculate the safest route (based on combined safety and distance)
        print("Calculating safest route...")
        safest_route = nx.shortest_path(G, start_node, end_node, weight='safe_weight')
    except nx.NetworkXNoPath:
        print(f"Error: No path found between the start and end points.")
        print(f"The network might be disconnected or the radius ({radius}m) might be too small.")
        print("Try using a different start/end point or increasing the radius.")
        return
    
    # Check for empty routes
    if len(shortest_route) <= 1 or len(safest_route) <= 1:
        print("Error: Route calculation failed - route contains only one node.")
        print("Suggestion: Try different start/end points or increase the radius.")
        return
    
    # Calculate route statistics
    shortest_length = sum(G.edges[u, v, 0]['length'] for u, v in zip(shortest_route[:-1], shortest_route[1:]))
    safest_length = sum(G.edges[u, v, 0]['length'] for u, v in zip(safest_route[:-1], safest_route[1:]))
    
    shortest_safety = sum(G.edges[u, v, 0]['safety_score'] for u, v in zip(shortest_route[:-1], shortest_route[1:])) / len(shortest_route[:-1])
    safest_safety = sum(G.edges[u, v, 0]['safety_score'] for u, v in zip(safest_route[:-1], safest_route[1:])) / len(safest_route[:-1])
    
    print(f"\nRoute Statistics:")
    print(f"Shortest route: {shortest_length:.0f} meters, avg safety score: {shortest_safety:.2f}/10")
    print(f"Safest route: {safest_length:.0f} meters, avg safety score: {safest_safety:.2f}/10")
    print(f"Safety improvement: {safest_safety - shortest_safety:.2f} points")
    print(f"Distance increase: {safest_length - shortest_length:.0f} meters ({(safest_length/shortest_length - 1)*100:.1f}%)")
    
    # Create route analyses dictionaries for the visualizer
    shortest_analysis = {
        'total_length': shortest_length,
        'average_safety_score': shortest_safety
    }
    
    safest_analysis = {
        'total_length': safest_length,
        'average_safety_score': safest_safety
    }
    
    # Prepare routes and analyses for the visualizer
    routes = {
        'shortest': shortest_route,
        'safest': safest_route
    }
    
    route_analyses = {
        'shortest': shortest_analysis,
        'safest': safest_analysis
    }
    
    # Use the RouteVisualizer to create the visualization
    print("Generating map visualization...")
    visualizer = RouteVisualizer()
    
    # Create a figure and axes
    fig, ax = plt.subplots(1, 2, figsize=(15, 8))
    
    # Manually call the plot methods to avoid showing the interactive plot
    visualizer._plot_route(G, shortest_route, shortest_analysis, ax[0], "Shortest Route")
    visualizer._plot_route(G, safest_route, safest_analysis, ax[1], "Safest Route")
    
    plt.tight_layout()
    
    # Save the figure with high resolution
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"\nDetailed map saved as '{output_file}'")
    else:
        # If no output file specified, save to a default location
        default_output = f"route_map_{start_lat:.4f}_{start_lon:.4f}_to_{end_lat:.4f}_{end_lon:.4f}.png"
        plt.savefig(default_output, dpi=300, bbox_inches='tight')
        print(f"\nDetailed map saved as '{default_output}'")
    
    # Close the figure to prevent display
    plt.close(fig)
    
    print(f"\nTotal execution time: {time.time() - start_time:.2f} seconds")

def main():
    parser = argparse.ArgumentParser(description='Plot shortest and safest routes between two points')
    parser.add_argument('--start', type=str, required=True, help='Starting point as lat,lon')
    parser.add_argument('--end', type=str, required=True, help='Ending point as lat,lon')
    parser.add_argument('--radius', type=int, default=800, help='Network radius in meters')
    parser.add_argument('--output', type=str, help='Output file path for the map')
    
    args = parser.parse_args()
    
    # Parse the start and end points
    try:
        start_lat, start_lon = map(float, args.start.split(','))
        end_lat, end_lon = map(float, args.end.split(','))
    except ValueError:
        print("Error: Start and end points must be in the format lat,lon")
        return
    
    plot_routes(start_lat, start_lon, end_lat, end_lon, args.radius, args.output)

if __name__ == "__main__":
    main()
