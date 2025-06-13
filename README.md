# Safe Route Finder

A Python application that finds safe walking routes by considering various safety factors including crime rates, lighting, time of day, and nearby points of interest.

## Features

- Calculates both shortest and safest routes between two points
- Considers multiple safety factors:
  - Crime rates by LSOA
  - Street lighting
  - Time of day
  - Nearby POIs (police stations, hospitals, etc.)
  - Road types
- Provides detailed route analysis and visualization

## Installation

1. Clone this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Project Structure

- `src/` - Main source code
  - `data/` - Data loading and processing
  - `safety/` - Safety scoring and analysis
  - `routing/` - Route calculation
  - `visualization/` - Route visualization
- `config/` - Configuration files
- `main.py` - Application entry point

## Usage

```python
from src.main import SafeRouteFinder

finder = SafeRouteFinder()
route = finder.find_route(start_point=(51.5415, -0.1468), 
                         end_point=(51.5390, -0.1426))
route.visualize()
```
