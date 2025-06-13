"""
Script to visualize shortest and safest routes between two points using RouteVisualizer
"""
import matplotlib
# Force matplotlib to use a non-interactive backend
matplotlib.use('Agg')

import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
import argparse
import time
import sys
import os

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Import project modules
from src.data.data_loader import DataLoader
from src.safety.safety_scorer import SafetyScorer
from src.visualization.route_visualizer import RouteVisualizer

def visualize_routes(start_lat, start_lon, end_lat, end_lon, radius=800, output_file=None):
    """
    Visualize the shortest and safest routes between two points using RouteVisualizer.
    
    Args:
        start_lat: Starting point latitude
        start_lon: Starting point longitude
        end_lat: Ending point latitude
        end_lon: Ending point longitude
        radius: Network radius in meters
        output_file: Optional output file path for the map
    """
    print(f"Visualizing routes from ({start_lat}, {start_lon}) to ({end_lat}, {end_lon})")
    start_time = time.time()
    
    # Define center point (midpoint between start and end)
    center_lat = (start_lat + end_lat) / 2
    center_lon = (start_lon + end_lon) / 2
    
    # Initialize data loader and safety scorer
    print("Initializing data loader and safety scorer...")
    data_loader = DataLoader()
    safety_scorer = SafetyScorer(data_loader)
    
    # Load the street network
    print(f"Loading street network with {radius}m radius...")
    G = ox.graph_from_point((center_lat, center_lon), dist=radius, network_type='walk', simplify=True)
    print(f"Network has {len(G.nodes)} nodes and {len(G.edges)} edges")
    
    # Project the graph to use meters (important for proper display)
    G = ox.project_graph(G)
    
    # Load safety POIs
    safety_pois = data_loader.load_safety_pois((center_lat, center_lon), dist=radius)
    
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
    
    # Print safety score statistics
    if safety_scores:
        print(f"\nSafety Score Statistics:")
        print(f"Min: {min(safety_scores):.2f}")
        print(f"Max: {max(safety_scores):.2f}")
        print(f"Avg: {sum(safety_scores)/len(safety_scores):.2f}")
        print(f"Number of zero scores: {safety_scores.count(0)}/{len(safety_scores)}")
    else:
        print("Warning: No safety scores calculated!")
    
    # Find the nearest nodes to our start and end points
    start_node = ox.distance.nearest_nodes(G, start_lon, start_lat)
    end_node = ox.distance.nearest_nodes(G, end_lon, end_lat)
    
    # Calculate the shortest route (based only on distance)
    print("Calculating shortest route...")
    shortest_route = nx.shortest_path(G, start_node, end_node, weight='length')
    
    # Calculate the safest route (based on combined safety and distance)
    print("Calculating safest route...")
    safest_route = nx.shortest_path(G, start_node, end_node, weight='safe_weight')
    
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
    
    # Create a figure and axes for side-by-side visualization
    fig, ax = plt.subplots(1, 2, figsize=(15, 8))
    
    # Manually call the plot methods to avoid showing the interactive plot
    visualizer._plot_route(G, shortest_route, shortest_analysis, ax[0], "Shortest Route", safety_pois)
    visualizer._plot_route(G, safest_route, safest_analysis, ax[1], "Safest Route", safety_pois)
    
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
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Visualize shortest and safest routes between two points')
    parser.add_argument('--start', type=str, required=True, help='Starting point as "lat,lon"')
    parser.add_argument('--end', type=str, required=True, help='Ending point as "lat,lon"')
    parser.add_argument('--radius', type=int, default=800, help='Network radius in meters (default: 800)')
    parser.add_argument('--output', type=str, help='Output file path for the map')
    
    args = parser.parse_args()
    
    # Parse coordinates
    try:
        start_lat, start_lon = map(float, args.start.split(','))
        end_lat, end_lon = map(float, args.end.split(','))
    except ValueError:
        print("Error: Coordinates must be in the format 'lat,lon'")
        return
    
    # Visualize routes
    visualize_routes(start_lat, start_lon, end_lat, end_lon, args.radius, args.output)

if __name__ == "__main__":
    main()
