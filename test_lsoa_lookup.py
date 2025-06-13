"""
Test script to verify LSOA lookup functionality
"""
import geopandas as gpd
from shapely.geometry import Point
import pandas as pd
from src.data.data_loader import DataLoader

def main():
    print("Testing LSOA lookup functionality...")
    
    # Initialize DataLoader
    data_loader = DataLoader()
    
    # Test coordinates (central London locations)
    test_points = [
        {"name": "Trafalgar Square", "lat": 51.508, "lon": -0.128},
        {"name": "Tower Bridge", "lat": 51.505, "lon": -0.075},
        {"name": "Camden Town", "lat": 51.539, "lon": -0.142},
        {"name": "Canary Wharf", "lat": 51.505, "lon": -0.023}
    ]
    
    # Test LSOA lookup for each point
    results = []
    for point in test_points:
        lsoa = data_loader.get_lsoa_for_coordinate(point["lat"], point["lon"])
        
        # Get safety scores for this LSOA
        safety_scores = data_loader.load_lsoa_crime_data().get(lsoa, {})
        comparison_score = safety_scores.get('comparison_score', 'N/A')
        routing_score = safety_scores.get('routing_score', 'N/A')
        
        results.append({
            "Location": point["name"],
            "Latitude": point["lat"],
            "Longitude": point["lon"],
            "LSOA": lsoa,
            "Comparison Score": comparison_score,
            "Routing Score": routing_score
        })
    
    # Display results as a table
    results_df = pd.DataFrame(results)
    print("\nLSOA Lookup Results:")
    print(results_df.to_string(index=False))

if __name__ == "__main__":
    main()
