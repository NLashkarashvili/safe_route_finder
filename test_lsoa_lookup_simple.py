"""
Simplified test script to verify LSOA lookup functionality
"""
import geopandas as gpd
from shapely.geometry import Point
import pandas as pd

def main():
    print("Testing LSOA lookup functionality...")
    
    # Load LSOA boundaries
    try:
        lsoa_boundaries = gpd.read_file('C:/Users/Nineli.Lashkarashvil/SperryRail/Innovation/data_science/CPD/safe_route_finder/lsoa_geojson_map.geojson')
        print(f"Successfully loaded LSOA boundaries with {len(lsoa_boundaries)} polygons")
        
        # Print column names to identify LSOA code column
        print(f"Available columns: {lsoa_boundaries.columns.tolist()}")
        
        # Determine which column contains LSOA codes
        possible_lsoa_columns = ['LSOA11CD', 'lsoa11cd', 'LSOA_CODE', 'lsoa_code', 'id', 'ID', 'code', 'CODE']
        lsoa_code_column = None
        
        for col in possible_lsoa_columns:
            if col in lsoa_boundaries.columns:
                lsoa_code_column = col
                break
        
        if lsoa_code_column:
            print(f"Using column '{lsoa_code_column}' for LSOA codes")
            # Show a few sample values
            print(f"Sample LSOA codes: {lsoa_boundaries[lsoa_code_column].head().tolist()}")
        else:
            print("Could not identify LSOA code column. Available columns are:")
            for col in lsoa_boundaries.columns:
                print(f"  - {col}")
        
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
            # Create a point from the coordinates
            pt = Point(point["lon"], point["lat"])  # GeoJSON uses (longitude, latitude) order
            
            # Create a GeoDataFrame with the point
            point_gdf = gpd.GeoDataFrame(geometry=[pt], crs="EPSG:4326")
            
            # Perform spatial join to find which LSOA contains the point
            join = gpd.sjoin(point_gdf, lsoa_boundaries, how="left", predicate="within")
            
            # Get the LSOA code
            lsoa = None
            if not join.empty and lsoa_code_column in join.columns and not join[lsoa_code_column].isna().all():
                lsoa = join[lsoa_code_column].iloc[0]
            else:
                # Fallback to nearest if point is not within any LSOA
                distances = lsoa_boundaries.geometry.distance(pt)
                nearest_idx = distances.idxmin()
                lsoa = lsoa_boundaries.iloc[nearest_idx][lsoa_code_column]
            
            results.append({
                "Location": point["name"],
                "Latitude": point["lat"],
                "Longitude": point["lon"],
                "LSOA": lsoa
            })
        
        # Display results as a table
        results_df = pd.DataFrame(results)
        print("\nLSOA Lookup Results:")
        print(results_df.to_string(index=False))
        
    except Exception as e:
        print(f"Error loading or processing LSOA boundaries: {e}")

if __name__ == "__main__":
    main()
