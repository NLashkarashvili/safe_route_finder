import pandas as pd
import numpy as np
from dateutil.relativedelta import relativedelta
from datetime import datetime
# Load historical crime data
historical_file_path = 'c:/Users/Nineli.Lashkarashvil/SperryRail/Innovation/data_science/CPD/safe_route_finder/crime/crime/MPS LSOA Level Crime (Historical).csv'
historical_data = pd.read_csv(historical_file_path)

# Load recent crime data
recent_file_path = 'c:/Users/Nineli.Lashkarashvil/SperryRail/Innovation/data_science/CPD/safe_route_finder/crime/crime/MPS LSOA Level Crime (most recent 24 months).csv'
recent_data = pd.read_csv(recent_file_path)

# Define risky and less risky crime categories
risky_categories = ['DRUG OFFENCES', 'BURGLARY', 'MISCELLANEOUS CRIMES AGAINST SOCIETY', 'POSSESSION OF WEAPONS', 'PUBLIC ORDER OFFENCES', 'THEFT', 'VIOLENCE AGAINST THE PERSON']

# Add a new column to categorize crimes
historical_data['Risk Category'] = historical_data['Major Category'].apply(lambda x: 'Risky' if x in risky_categories else 'Less Risky')
recent_data['Risk Category'] = recent_data['Major Category'].apply(lambda x: 'Risky' if x in risky_categories else 'Less Risky')

# Combine historical and recent data
combined_data = pd.concat([historical_data, recent_data], ignore_index=True)

# Extract date columns
historical_date_columns = [col for col in historical_data.columns if col.isdigit()]
recent_date_columns = [col for col in recent_data.columns if col.isdigit()]

# Group by LSOA and Risk Category, sum over date columns
historical_grouped = historical_data.groupby(['LSOA Code', 'Risk Category'])[historical_date_columns].sum().reset_index()
recent_grouped = recent_data.groupby(['LSOA Code', 'Risk Category'])[recent_date_columns].sum().reset_index()

# Merge historical and recent grouped data without filling
combined_grouped = pd.merge(historical_grouped, recent_grouped, on=['LSOA Code', 'Risk Category'], how='outer')

# Sort date columns after combining and grouping
date_columns = sorted([col for col in combined_grouped.columns if col.isdigit()])
combined_grouped = combined_grouped[['LSOA Code', 'Risk Category'] + date_columns]

# Combine risky and less risky scores for each date column
for date_col in date_columns:
    combined_grouped[date_col] = combined_grouped.apply(lambda row: row[date_col] if row['Risk Category'] == 'Risky' else 0.5 * row[date_col], axis=1)

# Calculate exponential decay for each date column
combined_grouped = combined_grouped.groupby('LSOA Code')[date_columns].sum().reset_index()
reference_date = datetime(2025, 2, 1)
print(combined_grouped.head())
lambda_decay = 0.05
for date_col in date_columns:
    # Parse year and month from column name
    col_year = int(date_col[:4])
    col_month = int(date_col[4:6])
    col_date = datetime(col_year, col_month, 1)

    # Calculate number of months between the column date and reference
    delta_months = (reference_date.year - col_date.year) * 12 + (reference_date.month - col_date.month)

    # Apply exponential decay
    decay_factor = np.exp(-lambda_decay * delta_months)
    combined_grouped[date_col] = combined_grouped[date_col] * decay_factor

print(combined_grouped.head())
# Sum decayed scores for each LSOA
combined_grouped["Total_Decayed_Score"] = combined_grouped[date_columns].sum(axis=1)
combined_grouped = combined_grouped[['LSOA Code', 'Total_Decayed_Score']]
# Ensure unique decayed score for each LSOA
# unique_decayed_scores = combined_grouped.groupby('LSOA Code')['Decayed Combined Score'].sum().reset_index()

# # Apply z-score normalization to the unique decayed scores
mean_decayed = combined_grouped['Total_Decayed_Score'].mean()
std_decayed = combined_grouped['Total_Decayed_Score'].std()
combined_grouped['Z-Score_Decayed'] = (combined_grouped['Total_Decayed_Score'] - mean_decayed) / std_decayed
print(combined_grouped.head())

combined_grouped.to_csv('combined_scores.csv', index=False)
print('Combined scores saved as combined_scores.csv')
