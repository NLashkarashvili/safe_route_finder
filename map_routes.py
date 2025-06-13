"""
Script to create a map visualization of safe routes in Camden
"""
import matplotlib
# Force matplotlib to use a non-interactive backend
matplotlib.use('Agg')

import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
import argparse
import time
import sys
import os
import datetime
from shapely.geometry import Point

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Import project modules
from src.data.data_loader import DataLoader
from src.safety.safety_scorer import SafetyScorer

def create_route_map(start_lat, start_lon, end_lat, end_lon, radius=800, output_file=None):
    """
    Create a map visualization of the shortest and safest routes.
    
    Args:
        start_lat: Starting point latitude
        start_lon: Starting point longitude
        end_lat: Ending point latitude
        end_lon: Ending point longitude
        radius: Network radius in meters
        output_file: Optional output file path for the map
    """
    print(f"Creating route map from ({start_lat}, {start_lon}) to ({end_lat}, {end_lon})")
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
    
    # Project the graph to use meters
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
    
    # Create a single map visualization
    print("Generating map visualization...")
    
    # Create a figure
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # Plot the base map
    ox.plot_graph(G, ax=ax, node_size=0, edge_linewidth=0.5, edge_color='#999999', bgcolor='w')
    
    # Create safety colormap
    safety_colors = [
        (0.8, 0.0, 0.0),  # Red for dangerous
        (1.0, 0.65, 0.0),  # Orange for moderate
        (0.0, 0.8, 0.0)    # Green for safe
    ]
    safety_cmap = LinearSegmentedColormap.from_list('safety', safety_colors)
    
    # Plot the shortest route in blue
    shortest_line = []
    for u, v in zip(shortest_route[:-1], shortest_route[1:]):
        x1, y1 = G.nodes[u]['x'], G.nodes[u]['y']
        x2, y2 = G.nodes[v]['x'], G.nodes[v]['y']
        ax.plot([x1, x2], [y1, y2], color='blue', linewidth=4, alpha=0.7, zorder=3)
        shortest_line.append((x1, y1))
    shortest_line.append((x2, y2))
    
    # Plot the safest route with safety coloring
    for u, v in zip(safest_route[:-1], safest_route[1:]):
        edge_data = G[u][v][0]
        safety_score = edge_data['safety_score']
        color = safety_cmap(safety_score / 10)
        
        x1, y1 = G.nodes[u]['x'], G.nodes[u]['y']
        x2, y2 = G.nodes[v]['x'], G.nodes[v]['y']
        ax.plot([x1, x2], [y1, y2], color='green', linewidth=4, alpha=0.7, zorder=4)
    
    # Plot POIs
    if not safety_pois.empty:
        print("Adding POIs to the map...")
        # Filter to important POI types
        important_pois = safety_pois[
            safety_pois['amenity'].isin(['police', 'hospital', 'pharmacy', 'bar', 'pub', 'nightclub']) | 
            safety_pois['leisure'].isin(['park', 'garden']) |
            safety_pois['public_transport'].notna()
        ]
        
        # Create POI categories for different markers
        poi_categories = {
            'safe': ['police', 'hospital', 'pharmacy'],
            'caution': ['bar', 'pub', 'nightclub'],
            'leisure': ['park', 'garden'],
            'transport': ['station', 'stop', 'platform']
        }
        
        # Plot each category with different markers
        for category, amenities in poi_categories.items():
            if category == 'transport':
                category_pois = important_pois[important_pois['public_transport'].notna()]
            else:
                category_pois = important_pois[important_pois['amenity'].isin(amenities) | 
                                              important_pois['leisure'].isin(amenities)]
            
            if not category_pois.empty:
                marker = {
                    'safe': '^',  # Triangle for safe POIs
                    'caution': 's',  # Square for caution POIs
                    'leisure': 'p',  # Pentagon for leisure
                    'transport': 'o'  # Circle for transport
                }.get(category, 'o')
                
                color = {
                    'safe': 'green',
                    'caution': 'red',
                    'leisure': 'lightgreen',
                    'transport': 'blue'
                }.get(category, 'gray')
                
                # Get coordinates from the GeoDataFrame
                x = [geom.x for geom in category_pois.geometry]
                y = [geom.y for geom in category_pois.geometry]
                
                # Plot POIs as markers
                ax.scatter(x, y, color=color, marker=marker, s=50, alpha=0.7, zorder=5)
    
    # Add start and end markers
    ax.scatter(G.nodes[start_node]['x'], G.nodes[start_node]['y'], 
              c='blue', s=100, zorder=6, marker='o', edgecolor='black', linewidth=1.5)
    ax.scatter(G.nodes[end_node]['x'], G.nodes[end_node]['y'], 
              c='red', s=100, zorder=6, marker='o', edgecolor='black', linewidth=1.5)
    
    # Add annotations for start and end
    ax.annotate('Start', xy=(G.nodes[start_node]['x'], G.nodes[start_node]['y']), 
                xytext=(10, 10), textcoords="offset points", 
                fontsize=12, fontweight='bold', color='blue')
    ax.annotate('End', xy=(G.nodes[end_node]['x'], G.nodes[end_node]['y']), 
                xytext=(10, 10), textcoords="offset points", 
                fontsize=12, fontweight='bold', color='red')
    
    # Create legend
    legend_elements = [
        mpatches.Patch(color='blue', label=f'Shortest Route ({shortest_length:.0f}m, Safety: {shortest_safety:.1f}/10)'),
        mpatches.Patch(color='green', label=f'Safest Route ({safest_length:.0f}m, Safety: {safest_safety:.1f}/10)'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', markersize=10, label='Start'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markersize=10, label='End'),
        plt.Line2D([0], [0], marker='^', color='w', markerfacecolor='green', markersize=10, label='Safe (Police/Hospital)'),
        plt.Line2D([0], [0], marker='s', color='w', markerfacecolor='red', markersize=10, label='Caution (Bar/Club)'),
        plt.Line2D([0], [0], marker='p', color='w', markerfacecolor='lightgreen', markersize=10, label='Park/Garden'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', markersize=10, label='Transport POI')
    ]
    
    # Add legend in a good position
    ax.legend(handles=legend_elements, loc='lower left', fontsize=10, framealpha=0.8)
    
    # Add title with current date and time
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    time_of_day = "Day" if 6 <= datetime.datetime.now().hour < 20 else "Night"
    plt.title(f"Pedestrian Safety Routing: Camden Market to Camden Town Station\n{current_time} - {time_of_day}", 
              fontsize=14)
    
    # Add safety factors info box
    safety_info = (
        "Safety factors at " + current_time + ":\n"
        "- Parks: Safer\n"
        "- Nightlife: Neutral\n"
        "- Transit: Safer\n"
        "- Street lighting: Less important"
    )
    
    # Add text box for safety factors
    props = dict(boxstyle='round', facecolor='white', alpha=0.8)
    ax.text(0.02, 0.02, safety_info, transform=ax.transAxes, fontsize=9,
            verticalalignment='bottom', bbox=props)
    
    # Improve figure appearance
    plt.tight_layout()
    
    # Save the figure with high resolution
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"\nDetailed map saved as '{output_file}'")
    else:
        # If no output file specified, save to a default location
        default_output = f"camden_safety_map_{current_time.replace(':', '-').replace(' ', '_')}.png"
        plt.savefig(default_output, dpi=300, bbox_inches='tight')
        print(f"\nDetailed map saved as '{default_output}'")
    
    # Close the figure to prevent display
    plt.close(fig)
    
    print(f"\nTotal execution time: {time.time() - start_time:.2f} seconds")

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Create a map visualization of safe routes in Camden')
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
    
    # Create route map
    create_route_map(start_lat, start_lon, end_lat, end_lon, args.radius, args.output)

if __name__ == "__main__":
    main()
