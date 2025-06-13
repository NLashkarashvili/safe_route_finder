"""
Basic script to plot shortest and safest routes between two points
"""
import matplotlib
# Force matplotlib to use a non-interactive backend
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import argparse
import time
import sys
import os
import datetime

def plot_basic_routes(start_lat, start_lon, end_lat, end_lon, output_file=None):
    """
    Create a basic plot of the shortest and safest routes.
    
    Args:
        start_lat: Starting point latitude
        start_lon: Starting point longitude
        end_lat: Ending point latitude
        end_lon: Ending point longitude
        output_file: Optional output file path for the plot
    """
    print(f"Creating basic route plot from ({start_lat}, {start_lon}) to ({end_lat}, {end_lon})")
    
    # Example route data (replace with your actual route data)
    # This is just a simple example with straight lines
    shortest_route = [
        (start_lon, start_lat),
        (end_lon, end_lat)
    ]
    
    # Create a slight detour for the "safest" route
    mid_lon = (start_lon + end_lon) / 2
    mid_lat = (start_lat + end_lat) / 2
    # Add a small offset to create a different path
    offset = 0.002  # About 200 meters
    safest_route = [
        (start_lon, start_lat),
        (mid_lon + offset, mid_lat + offset),
        (end_lon, end_lat)
    ]
    
    # Example statistics (replace with your actual data)
    shortest_length = 2073  # meters
    safest_length = 2200  # meters
    shortest_safety = 1.52  # out of 10
    safest_safety = 2.30  # out of 10
    
    print(f"\nRoute Statistics:")
    print(f"Shortest route: {shortest_length:.0f} meters, avg safety score: {shortest_safety:.2f}/10")
    print(f"Safest route: {safest_length:.0f} meters, avg safety score: {safest_safety:.2f}/10")
    print(f"Safety improvement: {safest_safety - shortest_safety:.2f} points")
    print(f"Distance increase: {safest_length - shortest_length:.0f} meters ({(safest_length/shortest_length - 1)*100:.1f}%)")
    
    # Create a figure
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Extract route coordinates
    shortest_x = [point[0] for point in shortest_route]
    shortest_y = [point[1] for point in shortest_route]
    safest_x = [point[0] for point in safest_route]
    safest_y = [point[1] for point in safest_route]
    
    # Plot routes
    ax.plot(shortest_x, shortest_y, 'b-', linewidth=3, label=f'Shortest ({shortest_length:.0f}m, Safety: {shortest_safety:.1f}/10)')
    ax.plot(safest_x, safest_y, 'g-', linewidth=3, label=f'Safest ({safest_length:.0f}m, Safety: {safest_safety:.1f}/10)')
    
    # Plot start and end points
    ax.plot(start_lon, start_lat, 'ro', markersize=10, label='Start')
    ax.plot(end_lon, end_lat, 'mo', markersize=10, label='End')
    
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
        print(f"\nBasic plot saved as '{output_file}'")
    else:
        # If no output file specified, save to a default location
        default_output = f"basic_route_plot_{current_time.replace(':', '-').replace(' ', '_')}.png"
        plt.savefig(default_output, dpi=300, bbox_inches='tight')
        print(f"\nBasic plot saved as '{default_output}'")
    
    # Close the figure to prevent display
    plt.close(fig)

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Create a basic plot of safe routes in Camden')
    parser.add_argument('--start', type=str, required=True, help='Starting point as "lat,lon"')
    parser.add_argument('--end', type=str, required=True, help='Ending point as "lat,lon"')
    parser.add_argument('--output', type=str, help='Output file path for the plot')
    
    args = parser.parse_args()
    
    # Parse coordinates
    try:
        start_lat, start_lon = map(float, args.start.split(','))
        end_lat, end_lon = map(float, args.end.split(','))
    except ValueError:
        print("Error: Coordinates must be in the format 'lat,lon'")
        return
    
    # Create route plot
    plot_basic_routes(start_lat, start_lon, end_lat, end_lon, args.output)

if __name__ == "__main__":
    main()
