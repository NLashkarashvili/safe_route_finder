"""
Simplified test script for safe route finding
"""
import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np

def main():
    print("Testing simplified safe route finding...")
    
    # Define Camden area coordinates
    camden_center = (51.5390, -0.1426)  # Camden Town
    
    # Define start and end points for our route
    start_point = (51.5390, -0.1426)  # Camden Town
    end_point = (51.5305, -0.1240)    # King's Cross
    
    # Load a smaller street network
    print("Loading street network...")
    G = ox.graph_from_point(camden_center, dist=1000, network_type='walk', simplify=True)
    
    # Find the nearest nodes to our start and end points
    start_node = ox.distance.nearest_nodes(G, start_point[1], start_point[0])
    end_node = ox.distance.nearest_nodes(G, end_point[1], end_point[0])
    
    # Add mock safety scores (normally these would come from our safety scorer)
    print("Adding mock safety scores...")
    np.random.seed(42)  # For reproducibility
    
    for u, v, k, data in G.edges(keys=True, data=True):
        # Assign random safety scores between 0-10
        # In reality, these would be calculated based on crime data
        data['safety_score'] = np.random.uniform(0, 10)
        
        # Create a weight that combines distance and safety
        # Lower safety score = higher weight (to be avoided)
        data['safe_weight'] = data['length'] * (11 - data['safety_score'])
    
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
    
    # Plot the routes
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Plot the base map
    ox.plot_graph(G, ax=ax, node_size=0, edge_linewidth=0.5, edge_color='#999999')
    
    # Plot the shortest route
    ox.plot_graph_route(G, shortest_route, ax=ax, route_color='blue', route_linewidth=4, route_alpha=0.7)
    
    # Plot the safest route
    ox.plot_graph_route(G, safest_route, ax=ax, route_color='green', route_linewidth=4, route_alpha=0.7)
    
    # Add legend and title
    ax.legend(['Street Network', 'Shortest Route', 'Safest Route'], loc='best')
    plt.title('Camden Area: Shortest vs. Safest Route (Mock Data)')
    
    # Save the figure
    plt.savefig('simple_route_comparison.png', dpi=300, bbox_inches='tight')
    print("\nMap saved as 'simple_route_comparison.png'")
    
    # Show the plot
    plt.show()

if __name__ == "__main__":
    main()
