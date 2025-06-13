"""
Simple test script to verify POI loading and visualization.
"""
import osmnx as ox
import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
import sys
import os

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Import project modules
from src.data.data_loader import DataLoader

# Define test location (Central London)
center_lat = 51.5074
center_lon = -0.1278
center_point = (center_lat, center_lon)
radius = 1000  # meters

print(f"Testing POI loading for {center_point} with radius {radius}m")

# Initialize data loader
data_loader = DataLoader()

# Load POIs directly
print("Fetching POIs directly from OpenStreetMap...")
try:
    pois = ox.features_from_point(center_point, {
        'amenity': True,
        'leisure': True,
        'shop': True,
        'public_transport': True,
        'highway': ['street_lamp']
    }, dist=radius)
    
    if pois.empty:
        print("No POIs found!")
    else:
        print(f"Found {len(pois)} POIs")
        
        # Print column information
        print(f"POI columns: {pois.columns.tolist()}")
        
        # Count POIs by type
        if 'amenity' in pois.columns:
            print(f"Amenity counts: {pois['amenity'].value_counts().to_dict()}")
        if 'leisure' in pois.columns:
            print(f"Leisure counts: {pois['leisure'].value_counts().to_dict()}")
        if 'shop' in pois.columns:
            print(f"Shop counts: {pois['shop'].value_counts().to_dict()}")
        if 'public_transport' in pois.columns:
            print(f"Public transport counts: {pois['public_transport'].value_counts().to_dict()}")
        
        # Create a simple plot
        fig, ax = plt.subplots(figsize=(10, 10))
        
        # Plot base map
        base = ox.graph_from_point(center_point, dist=radius, network_type='walk')
        ox.plot_graph(base, ax=ax, node_size=0, edge_linewidth=0.5, 
                     edge_color='#999999', bgcolor='w', show=False, close=False)
        
        # Plot POIs
        for _, poi in pois.iterrows():
            if poi.geometry.geom_type == 'Point':
                x, y = poi.geometry.x, poi.geometry.y
                
                # Determine color based on type
                color = 'gray'  # default
                if 'amenity' in poi and poi['amenity'] in ['police', 'hospital', 'pharmacy']:
                    color = 'blue'
                elif 'amenity' in poi and poi['amenity'] in ['bar', 'pub', 'nightclub']:
                    color = 'red'
                elif 'leisure' in poi and poi['leisure'] in ['park', 'garden']:
                    color = 'green'
                
                # Plot the POI
                ax.scatter(x, y, color=color, s=100, zorder=5, 
                          edgecolor='black', linewidth=1.5)
        
        plt.title(f"POIs around {center_point} ({radius}m radius)")
        plt.tight_layout()
        plt.savefig("test_pois.png", dpi=300)
        print("Plot saved as test_pois.png")
        
except Exception as e:
    print(f"Error fetching POIs: {e}")

# Try using the data_loader method
print("\nTesting POI loading through DataLoader...")
try:
    safety_pois = data_loader.load_safety_pois(center_point, dist=radius)
    
    if safety_pois.empty:
        print("No POIs found through DataLoader!")
    else:
        print(f"Found {len(safety_pois)} POIs through DataLoader")
        print(f"POI columns: {safety_pois.columns.tolist()}")
        
        # Count POIs by safety type
        if 'safety_type' in safety_pois.columns:
            print(f"Safety type counts: {safety_pois['safety_type'].value_counts().to_dict()}")
        
        # Create a simple plot
        fig, ax = plt.subplots(figsize=(10, 10))
        
        # Plot base map
        base = ox.graph_from_point(center_point, dist=radius, network_type='walk')
        ox.plot_graph(base, ax=ax, node_size=0, edge_linewidth=0.5, 
                     edge_color='#999999', bgcolor='w', show=False, close=False)
        
        # Plot POIs by safety type
        for safety_type, color in [('positive', 'blue'), ('negative', 'red'), ('neutral', 'green')]:
            filtered = safety_pois[safety_pois['safety_type'] == safety_type]
            
            if not filtered.empty:
                print(f"Plotting {len(filtered)} {safety_type} POIs")
                for _, poi in filtered.iterrows():
                    if poi.geometry.geom_type == 'Point':
                        x, y = poi.geometry.x, poi.geometry.y
                        ax.scatter(x, y, color=color, s=100, zorder=5, 
                                  edgecolor='black', linewidth=1.5)
        
        plt.title(f"Safety POIs through DataLoader ({radius}m radius)")
        plt.tight_layout()
        plt.savefig("test_dataloader_pois.png", dpi=300)
        print("Plot saved as test_dataloader_pois.png")
        
except Exception as e:
    print(f"Error loading POIs through DataLoader: {e}")

print("\nTest complete!")
