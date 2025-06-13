"""
Crime scoring functionality based on population and national averages.
"""
import pandas as pd
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import Dict, List, Optional
import math


class CrimeScorer:
    def __init__(self, 
                 historical_file_path: str,
                 recent_file_path: str,
                 population_file_path: str,
                 national_average_per_1000: float = 90.0):
        """
        Initialize CrimeScorer with data paths and national average.
        
        Args:
            historical_file_path: Path to historical crime data CSV
            recent_file_path: Path to recent crime data CSV
            population_file_path: Path to LSOA population data
            national_average_per_1000: National average crime rate per 1000 people per year
        """
        self.national_average = national_average_per_1000
        self.reference_date = datetime.now()
        self.lambda_decay = 0.05  # Decay factor for routing scores
        
        # Define high-risk crime categories for routing only
        self.risky_categories = [
            'DRUG OFFENCES',
            'BURGLARY',
            'MISCELLANEOLES AGAINST SOCIETY',
            'POSSESSION OF WEAPONS',
            'PUBLIC ORDER OFFENCES',
            'THEFT',
            'VIOLENCE AGAINST THE PERSON'
        ]
        
        # Load data
        self.historical_data = pd.read_csv(historical_file_path)
        self.recent_data = pd.read_csv(recent_file_path)
        self.population_data = pd.read_csv(population_file_path)
        
        # Rename population columns to match expected format
        self.population_data = self.population_data.rename(columns={
            'Codes': 'LSOA Code',
            '2013': 'Population'
        })
        
        # Process crime data
        self._process_crime_data()

    def _process_crime_data(self):
        """Process and combine historical and recent crime data."""
        # Add risk categories (for routing only)
        self.historical_data['Risk Category'] = self.historical_data['Major Category'].apply(
            lambda x: 'Risky' if x in self.risky_categories else 'Less Risky'
        )
        self.recent_data['Risk Category'] = self.recent_data['Major Category'].apply(
            lambda x: 'Risky' if x in self.risky_categories else 'Less Risky'
        )

        # Combine data
        self.combined_data = pd.concat([self.historical_data, self.recent_data], ignore_index=True)
        
        # Get date columns
        self.date_columns = sorted([col for col in self.combined_data.columns if col.isdigit()])
        
        # Calculate both types of scores
        self._calculate_annual_scores()
        self._calculate_weighted_scores()

    def _calculate_annual_scores(self):
        """Calculate annual crime scores (most recent 12 months) for national average comparison."""
        # Get the most recent 12 months of data
        recent_months = sorted(self.date_columns)[-12:]
        
        # Simply sum all crimes by LSOA for national average comparison
        self.annual_lsoa_crimes = self.combined_data.groupby('LSOA Code')[recent_months].sum().sum(axis=1)

    def _calculate_weighted_scores(self):
        """Calculate time-weighted crime scores for routing purposes."""
        # Group by LSOA and Risk Category
        grouped = self.combined_data.groupby(['LSOA Code', 'Risk Category'])[self.date_columns].sum()
        
        # Apply risk weights and time decay
        grouped = grouped.reset_index()
        for date_col in self.date_columns:
            # Apply risk category weights (only for routing)
            grouped[date_col] = grouped.apply(
                lambda row: row[date_col] if row['Risk Category'] == 'Risky' 
                else 0.5 * row[date_col],
                axis=1
            )
            
            # Apply time decay
            col_year = int(date_col[:4])
            col_month = int(date_col[4:6])
            col_date = datetime(col_year, col_month, 1)
            months_diff = abs((self.reference_date.year - col_date.year) * 12 
                            + self.reference_date.month - col_date.month)
            decay_factor = np.exp(-self.lambda_decay * months_diff)
            grouped[date_col] *= decay_factor

        # Sum across risk categories
        self.weighted_lsoa_scores = grouped.groupby('LSOA Code')[self.date_columns].sum().sum(axis=1)

    def calculate_safety_score(self, lsoa_code: str) -> Dict[str, float]:
        """
        Calculate both comparison-based and routing safety scores for an LSOA.
        
        Args:
            lsoa_code: LSOA code to calculate score for
            
        Returns:
            Dict with both comparison and routing safety scores
        """
        try:
            # Get population for LSOA
            lsoa_population = self.population_data.loc[
                self.population_data['LSOA Code'] == lsoa_code,
                'Population'
            ].iloc[0]
            
            # Calculate annual crime rate per 1000 people (using all crimes)
            annual_crimes = self.annual_lsoa_crimes.get(lsoa_code, 0)
            annual_crime_rate = (annual_crimes / lsoa_population) * 1000
            
            # Simply divide local rate by national average to get the ratio
            # For comparison score: lower ratio = higher score (safer)
            ratio = annual_crime_rate / self.national_average if self.national_average > 0 else 0
            
            # Convert ratio to 0-10 scale for comparison score
            # ratio = 0 → score = 7 (safer than average)
            # ratio = 1 (national average) → score = 5
            # ratio = 3 → score = 1 (more dangerous)

            # Get weighted score for routing (using risk categories and time decay)
            weighted_crimes = self.weighted_lsoa_scores.get(lsoa_code, 0)
            weighted_crime_rate = (weighted_crimes / lsoa_population) * 1000
            
            # For routing: higher ratio = higher score (cost)
            # ratio = 0 → score = 3 (lower cost)
            # ratio = 1 (national average) → score = 5
            # ratio = 3 → score = 9 (higher cost)
            ratio = weighted_crime_rate / self.national_average if self.national_average > 0 else 0
            comparison_score = ratio
            routing_score = max(0, min(10, 5 + (2 * (ratio - 1))))
            
            return {
                'comparison_score': comparison_score,  # Based on raw crime counts
                'routing_score': routing_score,       # Based on weighted risks and time
                'annual_crime_rate': annual_crime_rate  # For reference
            }
            
        except (KeyError, IndexError):
            # Return default scores if LSOA not found
            return {
                'comparison_score': 5.0,
                'routing_score': 5.0,
                'annual_crime_rate': self.national_average
            }

    def get_all_safety_scores(self) -> Dict[str, Dict[str, float]]:
        """
        Calculate safety scores for all LSOAs.
        
        Returns:
            Dict mapping LSOA codes to their safety scores
        """
        return {
            lsoa: self.calculate_safety_score(lsoa)
            for lsoa in self.annual_lsoa_crimes.index
        }

    def save_safety_scores(self, output_path: str) -> None:
        """
        Save calculated safety scores to a CSV file.
        
        Args:
            output_path: Path where to save the CSV file
        """
        # Get all scores
        scores = self.get_all_safety_scores()
        
        # Convert to DataFrame for easy saving
        df = pd.DataFrame.from_dict(scores, orient='index')
        
        # Reset index to make LSOA code a column
        df.reset_index(inplace=True)
        df.rename(columns={'index': 'LSOA Code'}, inplace=True)
        
        # Ensure columns are in a good order
        column_order = [
            'LSOA Code',
            'comparison_score',
            'routing_score',
            'annual_crime_rate'
        ]
        df = df[column_order]
        
        # Save to CSV
        df.to_csv(output_path, index=False)
        print(f"Safety scores saved to {output_path}")
