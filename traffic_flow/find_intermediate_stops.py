import pandas as pd
import numpy as np
from math import radians, sin, cos, sqrt, atan2

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance between two points on Earth."""
    R = 6371  # Earth's radius in kilometers

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c
    
    return distance

def find_intermediate_stops(start_lat, start_lon, end_lat, end_lon, max_deviation_km=0.5):
    """
    Find bus stops that lie between two points within a specified deviation distance.
    
    Parameters:
    -----------
    start_lat, start_lon : float
        Latitude and longitude of the starting point
    end_lat, end_lon : float
        Latitude and longitude of the ending point
    max_deviation_km : float
        Maximum allowed deviation from the direct path in kilometers
        
    Returns:
    --------
    DataFrame containing the intermediate stops that meet the criteria
    """
    # Path to the CSV file
    naptan_path = r"C:\Users\Nineli.Lashkarashvil\SperryRail\Innovation\data_science\CPD\safe_route_finder\traffic_flow\Stops.csv"

    # Load and filter the DataFrame
    naptan_df = pd.read_csv(naptan_path)
    naptan_columns = ["NaptanCode", "Longitude", "Latitude", "ParentLocalityName", "LocalityName"]
    naptan_df = naptan_df[~(naptan_df['NaptanCode'].isnull()) & 
                         (naptan_df['Status']=="active")].reset_index(drop=True)
    naptan_df = naptan_df[(naptan_df['ParentLocalityName'].isin(["London", "City of London"]))][naptan_columns]
    
    # Calculate total distance between start and end points
    total_distance = haversine_distance(start_lat, start_lon, end_lat, end_lon)
    
    intermediate_stops = []
    
    for _, stop in naptan_df.iterrows():
        # Calculate distances
        d1 = haversine_distance(start_lat, start_lon, stop['Latitude'], stop['Longitude'])
        d2 = haversine_distance(stop['Latitude'], stop['Longitude'], end_lat, end_lon)
        
        # Check if the stop is roughly between the two points
        # The sum of distances through the stop should be close to the direct distance
        if abs((d1 + d2) - total_distance) < max_deviation_km:
            intermediate_stops.append({
                'NaptanCode': stop['NaptanCode'],
                'Latitude': stop['Latitude'],
                'Longitude': stop['Longitude'],
                'LocalityName': stop['LocalityName'],
                'Distance_from_start': d1,
                'Distance_from_end': d2
            })
    
    if not intermediate_stops:
        return pd.DataFrame()  # Return empty DataFrame if no stops found
    
    return pd.DataFrame(intermediate_stops)

# Example usage:
if __name__ == "__main__":
    # Example coordinates (these are sample London coordinates)
    start_lat, start_lon = 51.5074, -0.1278  # Central London
    end_lat, end_lon = 51.5173, -0.1162      # Kings Cross area
    
    result = find_intermediate_stops(start_lat, start_lon, end_lat, end_lon)
    if not result.empty:
        print("\nFound intermediate stops:")
        print(result)
    else:
        print("\nNo suitable intermediate stops found.")
