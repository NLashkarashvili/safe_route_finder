import pandas as pd
import numpy as np
from geopy.geocoders import Nominatim

# File paths
historical_file_path = 'c:/Users/Nineli.Lashkarashvil/SperryRail/Innovation/data_science/CPD/safe_route_finder/crime/crime/MPS LSOA Level Crime (Historical).csv'
recent_file_path = 'c:/Users/Nineli.Lashkarashvil/SperryRail/Innovation/data_science/CPD/safe_route_finder/crime/crime/MPS LSOA Level Crime (most recent 24 months).csv'

# Reading the historical LSOA level crime data
historical_data = pd.read_csv(historical_file_path)
print('Historical Data Loaded:', historical_data.shape)

# Display column names
print('Historical Data Columns:', historical_data.columns.tolist())

# Check number of unique LSOA codes
num_unique_lsoa = historical_data['LSOA Code'].nunique()
print(f'Number of Unique LSOA Codes: {num_unique_lsoa}')

# Unique major and minor categories
unique_categories = historical_data[['Major Category', 'Minor Category']].drop_duplicates()
print('Unique Major and Minor Categories:', unique_categories)

# Define risky and less risky crime categories
risky_categories = ['DRUG OFFENCES', 'BURGLARY', 'MISCELLANEOUS CRIMES AGAINST SOCIETY', 'POSSESSION OF WEAPONS', 'PUBLIC ORDER OFFENCES', 'THEFT', 'VIOLENCE AGAINST THE PERSON']

# Add a new column to categorize crimes
historical_data['Risk Category'] = historical_data['Major Category'].apply(lambda x: 'Risky' if x in risky_categories else 'Less Risky')

# Display statistics based on these groups
risk_stats = historical_data['Risk Category'].value_counts()
print('Updated Risk Category Statistics:', risk_stats)

# Reading the most recent 24 months LSOA level crime data
recent_data = pd.read_csv(recent_file_path)
print('Recent Data Loaded:', recent_data.shape)

# Display column names
print('Recent Data Columns:', recent_data.columns.tolist())

# Check number of unique LSOA codes in recent data
num_unique_lsoa_recent = recent_data['LSOA Code'].nunique()
print(f'Number of Unique LSOA Codes in Recent Data: {num_unique_lsoa_recent}')

# Extract date columns from historical and recent data
historical_date_columns = [col for col in historical_data.columns if col.isdigit()]
recent_date_columns = [col for col in recent_data.columns if col.isdigit()]

# Check for intersection of date columns
intersection_dates = set(historical_date_columns).intersection(set(recent_date_columns))
print('Intersection of Date Columns:', intersection_dates)

# Load the LSOA mapping data
lsoa_data_path = 'C:/Users/Nineli.Lashkarashvil/SperryRail/Innovation/data_science/CPD/safe_route_finder/crime/crime/PCD_OA_LSOA_MSOA_LAD_NOV22_UK_LU/PCD_OA_LSOA_MSOA_LAD_NOV22_UK_LU.csv'
lsoa_data = pd.read_csv(lsoa_data_path, encoding='ISO-8859-1')

# Print column names to identify the correct one
print('LSOA Data Columns:', lsoa_data.columns.tolist())

# Filter data for City of London using the correct column name
city_of_london_data = lsoa_data[lsoa_data['ladnm'] == 'City of London']
print('Filtered City of London Data:', city_of_london_data.head())

# Comment out geocoding section as we are using UK postcodes data directly
# geolocator = Nominatim(user_agent="geoapiExercises")
# city_of_london_data['Coordinates'] = city_of_london_data['pcds'].apply(lambda x: geolocator.geocode(x))
# city_of_london_data['Latitude'] = city_of_london_data['Coordinates'].apply(lambda x: x.latitude if x else None)
# city_of_london_data['Longitude'] = city_of_london_data['Coordinates'].apply(lambda x: x.longitude if x else None)

# Merge geocoded data with historical data on LSOA Code
# merged_data = historical_data.merge(city_of_london_data[['lsoa11cd', 'Latitude', 'Longitude']], left_on='LSOA Code', right_on='lsoa11cd', how='inner')

# Save the merged data for visualization
# merged_data.to_csv('c:/Users/Nineli.Lashkarashvil/SperryRail/Innovation/data_science/CPD/safe_route_finder/merged_crime_data.csv', index=False)

# Display a message indicating the data has been saved
# print('Merged data with coordinates saved for visualization.')

# Define weights for time-decay weighted sum
historical_weight = 0.5
recent_weight = 1.0

# Calculate weighted sum for historical data
historical_scores = historical_data[historical_date_columns].sum(axis=1) * historical_weight

# Calculate weighted sum for recent data
recent_scores = recent_data[recent_date_columns].sum(axis=1) * recent_weight

# Combine scores
combined_scores = historical_scores.add(recent_scores, fill_value=0)

# Add combined scores to historical data for reference
historical_data['Combined Score'] = combined_scores

# Display a sample of the combined scores
print('Sample Combined Scores:', historical_data[['LSOA Code', 'Combined Score']].head())

# Define decay rate
lambda_decay = 0.1

# Calculate time-decay weighted score
historical_scores = historical_data[historical_date_columns].apply(lambda row: sum(row[col] * np.exp(-lambda_decay * (2025 - int(col[:4])) * 12 + (4 - int(col[4:]))) for col in historical_date_columns), axis=1)
recent_scores = recent_data[recent_date_columns].apply(lambda row: sum(row[col] * np.exp(-lambda_decay * (2025 - int(col[:4])) * 12 + (4 - int(col[4:]))) for col in recent_date_columns), axis=1)

# Combine scores
combined_scores = historical_scores.add(recent_scores, fill_value=0)

# Add combined scores to historical data for reference
historical_data['Time-Decay Score'] = combined_scores

# Display a sample of the combined scores
print('Sample Time-Decay Scores:', historical_data[['LSOA Code', 'Time-Decay Score']].head())

# Assign weights
risky_weight = 1.0
less_risky_weight = 0.5

# Calculate weighted scores for Risky and Less Risky categories
risky_scores = historical_data[historical_data['Risk Category'] == 'Risky'][historical_date_columns].apply(lambda row: sum(row[col] * np.exp(-lambda_decay * (2025 - int(col[:4])) * 12 + (4 - int(col[4:]))) for col in historical_date_columns), axis=1) * risky_weight
less_risky_scores = historical_data[historical_data['Risk Category'] == 'Less Risky'][historical_date_columns].apply(lambda row: sum(row[col] * np.exp(-lambda_decay * (2025 - int(col[:4])) * 12 + (4 - int(col[4:]))) for col in historical_date_columns), axis=1) * less_risky_weight

# Add scores to historical data
historical_data.loc[historical_data['Risk Category'] == 'Risky', 'Risky Score'] = risky_scores
historical_data.loc[historical_data['Risk Category'] == 'Less Risky', 'Less Risky Score'] = less_risky_scores

# Calculate combined weighted score
historical_data['Combined Weighted Score'] = historical_data['Risky Score'].fillna(0) + historical_data['Less Risky Score'].fillna(0)

# Sum scores for Risky and Less Risky categories
historical_data['Total Score'] = historical_data['Risky Score'].fillna(0) + historical_data['Less Risky Score'].fillna(0)

# Apply exponential smoothing
alpha = 0.3  # Smoothing factor
historical_data['Smoothed Score'] = historical_data['Total Score'].ewm(alpha=alpha).mean()

# Correctly aggregate data by LSOA code
aggregated_data = historical_data.groupby('LSOA Code').agg({
    'Risky Score': 'sum',
    'Less Risky Score': 'sum',
    'Combined Weighted Score': 'sum',
    'Smoothed Score': 'sum'
}).reset_index()

# Determine which LSOA column has the most matches
lsoa_columns = ['oa11cd', 'lsoa11cd', 'msoa11cd', 'ladcd']
match_counts = {}
for col in lsoa_columns:
    match_counts[col] = lsoa_data[col].isin(aggregated_data['LSOA Code']).sum()

# Find the column with the most matches
best_lsoa_column = max(match_counts, key=match_counts.get)
print(f'LSOA column with most matches: {best_lsoa_column}')

# Load UK postcodes data
uk_postcodes_path = 'C:/Users/Nineli.Lashkarashvil/SperryRail/Innovation/data_science/CPD/safe_route_finder/ukpostcodes/ukpostcodes.csv'
uk_postcodes_data = pd.read_csv(uk_postcodes_path)

# Print column names of UK postcodes data to verify
print('UK Postcodes Data Columns:', uk_postcodes_data.columns.tolist())

# Check for missing postcodes
missing_postcodes = aggregated_data[~aggregated_data['LSOA Code'].isin(uk_postcodes_data['postcode'])]['LSOA Code'].unique()

# Print missing postcodes
print(f'Missing Postcodes: {missing_postcodes}')

# Save missing postcodes to a CSV file
missing_postcodes_df = pd.DataFrame(missing_postcodes, columns=['Missing Postcodes'])
missing_postcodes_df.to_csv('c:/Users/Nineli.Lashkarashvil/SperryRail/Innovation/data_science/CPD/safe_route_finder/missing_postcodes.csv', index=False)

# Print confirmation message
print('Missing postcodes saved to missing_postcodes.csv')

# Merge aggregated data with UK postcodes data using correct column names
merged_data = aggregated_data.merge(uk_postcodes_data[['postcode', 'latitude', 'longitude']], left_on='LSOA Code', right_on='postcode', how='inner')

# Save the merged data for visualization
merged_data.to_csv('c:/Users/Nineli.Lashkarashvil/SperryRail/Innovation/data_science/CPD/safe_route_finder/aggregated_crime_data.csv', index=False)

# Display a message indicating the data has been saved
print('Correctly aggregated data with coordinates saved for visualization.')

# Save the table to a CSV file
output_file_path = 'c:/Users/Nineli.Lashkarashvil/SperryRail/Innovation/data_science/CPD/safe_route_finder/crime_scores_smoothed.csv'
historical_data.to_csv(output_file_path, index=False)

# Display a message indicating the file has been saved
print(f'Smoothed crime scores saved to {output_file_path}')
