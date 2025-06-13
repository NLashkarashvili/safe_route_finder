"""
Test script to demonstrate safe route finding in Camden area
"""
import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString
import sys
import os
import time

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Import project modules
from src.data.data_loader import DataLoader
from src.safety.safety_scorer import SafetyScorer

def main():
    print("Testing safe route finding in Camden area...")
    start_time = time.time()
    
    # Define Camden area coordinates
    camden_center = (51.5390, -0.1426)  # Camden Town
    
    # Define start and end points for our route
    # Camden Town to King's Cross (shorter distance for testing)
    start_point = (51.5390, -0.1426)  # Camden Town
    end_point = (51.5330, -0.1290)    # Closer to King's Cross
    
    # Initialize our data loader and safety scorer
    print("Initializing data loader and safety scorer...")
    data_loader = DataLoader()
    safety_scorer = SafetyScorer(data_loader)
    print(f"Initialization took {time.time() - start_time:.2f} seconds")
    
    # Load the street network for Camden area (smaller radius, simplified)
    print("Loading street network for Camden area...")
    network_start = time.time()
    G = ox.graph_from_point(camden_center, dist=800, network_type='walk', simplify=True)
    print(f"Network loading took {time.time() - network_start:.2f} seconds")
    print(f"Network has {len(G.nodes)} nodes and {len(G.edges)} edges")
    
    # Load safety POIs (smaller radius)
    poi_start = time.time()
    safety_pois = data_loader.load_safety_pois(camden_center, dist=800)
    print(f"POI loading took {time.time() - poi_start:.2f} seconds")
    
    # Add safety scores to each edge in the graph
    print("Calculating safety scores for all edges...")
    safety_start = time.time()
    edge_count = 0
    for u, v, k, data in G.edges(keys=True, data=True):
        data['safety_score'] = safety_scorer.calculate_edge_safety(G, u, v, k, data, safety_pois)
        # Create a weight that combines distance and safety
        # Lower safety score = higher weight (to be avoided)
        data['safe_weight'] = data['length'] * (11 - data['safety_score'])
        edge_count += 1
        if edge_count % 100 == 0:
            print(f"Processed {edge_count}/{len(G.edges)} edges...")
    
    print(f"Safety scoring took {time.time() - safety_start:.2f} seconds")
    
    # Find the nearest nodes to our start and end points
    start_node = ox.distance.nearest_nodes(G, start_point[1], start_point[0])
    end_node = ox.distance.nearest_nodes(G, end_point[1], end_point[0])
    
    # Calculate the shortest route (based only on distance)
    print("Calculating shortest route...")
    route_start = time.time()
    shortest_route = nx.shortest_path(G, start_node, end_node, weight='length')
    print(f"Shortest route calculation took {time.time() - route_start:.2f} seconds")
    
    # Calculate the safest route (based on combined safety and distance)
    print("Calculating safest route...")
    safe_route_start = time.time()
    safest_route = nx.shortest_path(G, start_node, end_node, weight='safe_weight')
    print(f"Safest route calculation took {time.time() - safe_route_start:.2f} seconds")
    
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
    
    # Plot the routes
    print("Generating map visualization...")
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Plot the base map
    ox.plot_graph(G, ax=ax, node_size=0, edge_linewidth=0.5, edge_color='#999999')
    
    # Plot the shortest route
    ox.plot_graph_route(G, shortest_route, ax=ax, route_color='blue', route_linewidth=4, route_alpha=0.7)
    
    # Plot the safest route
    ox.plot_graph_route(G, safest_route, ax=ax, route_color='green', route_linewidth=4, route_alpha=0.7)
    
    # Add legend and title
    ax.legend(['Street Network', 'Shortest Route', 'Safest Route'], loc='best')
    plt.title('Camden Area: Shortest vs. Safest Route')
    
    # Save the figure
    plt.savefig('camden_safe_route_comparison.png', dpi=300, bbox_inches='tight')
    print("\nMap saved as 'camden_safe_route_comparison.png'")
    
    # Show the plot
    plt.show()
    
    print(f"\nTotal execution time: {time.time() - start_time:.2f} seconds")

if __name__ == "__main__":
    main()
