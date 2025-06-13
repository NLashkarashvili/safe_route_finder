from src.data.crime_scorer import CrimeScorer

# Initialize CrimeScorer with your data files
scorer = CrimeScorer(
    historical_file_path='c:/Users/Nineli.Lashkarashvil/SperryRail/Innovation/data_science/CPD/safe_route_finder/crime/crime/MPS LSOA Level Crime (Historical).csv',
    recent_file_path='c:/Users/Nineli.Lashkarashvil/SperryRail/Innovation/data_science/CPD/safe_route_finder/crime/crime/MPS LSOA Level Crime (most recent 24 months).csv',
    population_file_path='c:/Users/Nineli.Lashkarashvil/SperryRail/Innovation/data_science/CPD/safe_route_finder/lsoa_populations.csv'
)

# Save the scores to a different location
scorer.save_safety_scores("c:/Users/Nineli.Lashkarashvil/SperryRail/Innovation/data_science/CPD/safe_route_finder/output_safety_scores.csv")
