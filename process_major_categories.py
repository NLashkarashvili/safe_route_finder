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

# Extract date columns
historical_date_columns = [col for col in historical_data.columns if col.isdigit()]
recent_date_columns = [col for col in recent_data.columns if col.isdigit()]

# Combine historical and recent data
combined_data = pd.concat([historical_data, recent_data], ignore_index=True)

# Get unique major categories
major_categories = combined_data['Major Category'].unique()

# Process each major category separately
for category in major_categories:
    # Filter data for the current major category
    category_data = combined_data[combined_data['Major Category'] == category]
    
    # Group by LSOA and sum over date columns
    category_grouped = category_data.groupby('LSOA Code')[historical_date_columns + recent_date_columns].sum().reset_index()
    
    # Apply exponential decay
    reference_date = datetime(2025, 2, 1)
    lambda_decay = 0.05
    for date_col in historical_date_columns + recent_date_columns:
        col_year = int(date_col[:4])
        col_month = int(date_col[4:6])
        col_date = datetime(col_year, col_month, 1)
        delta_months = (reference_date.year - col_date.year) * 12 + (reference_date.month - col_date.month)
        decay_factor = np.exp(-lambda_decay * delta_months)
        category_grouped[date_col] = category_grouped[date_col] * decay_factor
    
    # Sum decayed scores for each LSOA
    category_grouped['Total_Decayed_Score'] = category_grouped[historical_date_columns + recent_date_columns].sum(axis=1)
    
    # Apply z-score normalization
    mean_decayed = category_grouped['Total_Decayed_Score'].mean()
    std_decayed = category_grouped['Total_Decayed_Score'].std()
    category_grouped['Z-Score_Decayed'] = (category_grouped['Total_Decayed_Score'] - mean_decayed) / std_decayed
    
    # Save to CSV
    file_name = f'z_score_decayed_{category.replace(" ", "_").lower()}.csv'
    category_grouped.to_csv(file_name, index=False)
    print(f'Saved {file_name}')
