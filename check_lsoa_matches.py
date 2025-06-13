import pandas as pd

# Load the LSOA mapping data
lsoa_data_path = 'C:/Users/Nineli.Lashkarashvil/SperryRail/Innovation/data_science/CPD/safe_route_finder/crime/crime/PCD_OA_LSOA_MSOA_LAD_NOV22_UK_LU/PCD_OA_LSOA_MSOA_LAD_NOV22_UK_LU.csv'
lsoa_data = pd.read_csv(lsoa_data_path, encoding='ISO-8859-1', engine='python')

# Load the crime data to get unique LSOA codes
crime_data_path = 'c:/Users/Nineli.Lashkarashvil/SperryRail/Innovation/data_science/CPD/safe_route_finder/crime_scores.csv'
crime_data = pd.read_csv(crime_data_path)

# Print the initial number of unique LSOAs in the crime data
initial_unique_lsoas = crime_data['LSOA Code'].nunique()
print(f'Initial number of unique LSOAs: {initial_unique_lsoas}')

# Use unique LSOA codes from crime data
unique_lsoa_codes = crime_data['LSOA Code'].unique()

# Determine which LSOA column has the most matches
lsoa_columns = ['oa11cd', 'lsoa11cd', 'msoa11cd', 'ladcd']
match_counts = {}
for col in lsoa_columns:
    match_counts[col] = lsoa_data[col].isin(unique_lsoa_codes).sum()

# Find the column with the most matches
best_lsoa_column = max(match_counts, key=match_counts.get)
print(f'LSOA column with most matches: {best_lsoa_column}')
print(f'Number of matches for {best_lsoa_column}: {match_counts[best_lsoa_column]}')

# Determine which LSOA column has the most unique matches
unique_match_counts = {}
for col in lsoa_columns:
    unique_match_counts[col] = lsoa_data[col].isin(unique_lsoa_codes).sum()

# Find the column with the most unique matches
best_unique_lsoa_column = max(unique_match_counts, key=unique_match_counts.get)
print(f'LSOA column with most unique matches: {best_unique_lsoa_column}')
print(f'Number of unique matches for {best_unique_lsoa_column}: {unique_match_counts[best_unique_lsoa_column]}')

# Check unique postcodes for matched LSOA codes
matched_lsoas = lsoa_data[lsoa_data[best_lsoa_column].isin(unique_lsoa_codes)]
unique_postcodes = matched_lsoas['pcds'].nunique()

# Print the number of unique postcodes
print(f'Number of unique postcodes for matched LSOA codes: {unique_postcodes}')

# Calculate the number of postcodes per LSOA
postcodes_per_lsoa = matched_lsoas.groupby('lsoa11cd')['pcds'].nunique()

# Identify LSOAs with no postcodes
lsoas_with_no_postcodes = postcodes_per_lsoa[postcodes_per_lsoa == 0].index

# Print a sample of LSOAs with no postcodes
print('Sample LSOAs with no postcodes:', lsoas_with_no_postcodes[:5].tolist())

# Print summary statistics
print('Summary of postcodes per LSOA:')
print(postcodes_per_lsoa.describe())
