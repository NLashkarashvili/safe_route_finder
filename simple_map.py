"""
Simple script to create a map visualization of safe routes in Camden
"""
import matplotlib
# Force matplotlib to use a non-interactive backend
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
import argparse
import time
import sys
import os
import datetime
import networkx as nx

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Import project modules
from src.data.data_loader import DataLoader
from src.safety.safety_scorer import SafetyScorer
from src.routing.route_finder import RouteFinder

def create_simple_map(start_lat, start_lon, end_lat, end_lon, output_file=None):
    """
    Create a simple map visualization of the shortest and safest routes.
    
    Args:
        start_lat: Starting point latitude
        start_lon: Starting point longitude
        end_lat: Ending point latitude
        end_lon: Ending point longitude
        output_file: Optional output file path for the map
    """
    print(f"Creating route map from ({start_lat}, {start_lon}) to ({end_lat}, {end_lon})")
    start_time = time.time()
    
    # Initialize data loader, safety scorer, and route finder
    print("Initializing components...")
    data_loader = DataLoader()
    safety_scorer = SafetyScorer(data_loader)
    route_finder = RouteFinder(safety_scorer)
    
    # Find routes
    print("Finding routes...")
    routes = route_finder.find_routes(
        start_lat=start_lat, 
        start_lon=start_lon,
        end_lat=end_lat,
        end_lon=end_lon
    )
    
    # Extract route data
    shortest_route = routes['shortest']['route']
    safest_route = routes['safest']['route']
    shortest_length = routes['shortest']['length']
    safest_length = routes['safest']['length']
    shortest_safety = routes['shortest']['safety_score']
    safest_safety = routes['safest']['safety_score']
    
    print(f"\nRoute Statistics:")
    print(f"Shortest route: {shortest_length:.0f} meters, avg safety score: {shortest_safety:.2f}/10")
    print(f"Safest route: {safest_length:.0f} meters, avg safety score: {safest_safety:.2f}/10")
    print(f"Safety improvement: {safest_safety - shortest_safety:.2f} points")
    print(f"Distance increase: {safest_length - shortest_length:.0f} meters ({(safest_length/shortest_length - 1)*100:.1f}%)")
    
    # Create a simple visualization
    print("Generating map visualization...")
    
    # Create a figure
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Extract route coordinates
    shortest_x = [node['x'] for node in shortest_route]
    shortest_y = [node['y'] for node in shortest_route]
    safest_x = [node['x'] for node in safest_route]
    safest_y = [node['y'] for node in safest_route]
    
    # Plot routes
    ax.plot(shortest_x, shortest_y, 'b-', linewidth=3, label=f'Shortest ({shortest_length:.0f}m, Safety: {shortest_safety:.1f}/10)')
    ax.plot(safest_x, safest_y, 'g-', linewidth=3, label=f'Safest ({safest_length:.0f}m, Safety: {safest_safety:.1f}/10)')
    
    # Plot start and end points
    ax.plot(shortest_x[0], shortest_y[0], 'ro', markersize=10, label='Start')
    ax.plot(shortest_x[-1], shortest_y[-1], 'mo', markersize=10, label='End')
    
    # Add legend
    ax.legend(loc='best')
    
    # Add title with current date and time
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    time_of_day = "Day" if 6 <= datetime.datetime.now().hour < 20 else "Night"
    plt.title(f"Pedestrian Safety Routing: Camden\n{current_time} - {time_of_day}", 
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
        print(f"\nMap saved as '{output_file}'")
    else:
        # If no output file specified, save to a default location
        default_output = f"camden_safety_map_{current_time.replace(':', '-').replace(' ', '_')}.png"
        plt.savefig(default_output, dpi=300, bbox_inches='tight')
        print(f"\nMap saved as '{default_output}'")
    
    # Close the figure to prevent display
    plt.close(fig)
    
    print(f"\nTotal execution time: {time.time() - start_time:.2f} seconds")

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Create a simple map visualization of safe routes in Camden')
    parser.add_argument('--start', type=str, required=True, help='Starting point as "lat,lon"')
    parser.add_argument('--end', type=str, required=True, help='Ending point as "lat,lon"')
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
    create_simple_map(start_lat, start_lon, end_lat, end_lon, args.output)

if __name__ == "__main__":
    main()
