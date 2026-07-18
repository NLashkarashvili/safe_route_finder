# Safe Route Finder

A Python application that finds **safe walking routes** in London by combining OpenStreetMap network data with crime statistics, street lighting, time-of-day awareness, and nearby points of interest.

## Motivation

Navigation apps optimise for speed or distance — but not personal safety. This tool computes an alternative "safest" route that avoids high-crime areas and prefers well-lit, populated streets, especially useful for walking at night.

## Features

- **Dual routing** — computes both shortest and safest paths between two points
- **Multi-factor safety scoring** per street segment:
  - Crime rates by LSOA (Lower Layer Super Output Area)
  - Street lighting / daylight status
  - Time of day (night penalty 8 PM–8 AM)
  - Proximity to POIs (police stations, hospitals, busy venues)
  - Road type (residential vs. main road vs. alley)
- **Interactive visualisation** — HTML map with colour-coded safety overlay
- **High-resolution static maps** — PNG exports for reports

## Tech Stack

- **OSMnx** — street network extraction from OpenStreetMap
- **NetworkX** — graph-based routing with custom edge weights
- **GeoPandas / Shapely** — spatial joins for LSOA lookups
- **Matplotlib** — static route visualisation
- **Pandas / NumPy** — data processing

## Installation

```bash
git clone https://github.com/NLashkarashvili/safe_route_finder.git
cd safe_route_finder
pip install -r requirements.txt
```

## Usage

```python
from src.main import SafeRouteFinder

finder = SafeRouteFinder()
result = finder.find_route(
    start_point=(51.5415, -0.1468),  # Camden Market
    end_point=(51.5390, -0.1426)     # Camden Town Station
)

# Print comparison
for route_type, analysis in result['analyses'].items():
    print(f"{route_type}: {analysis['total_length']:.0f}m, "
          f"safety: {analysis['average_safety_score']:.1f}/10")
```

## Project Structure

```
├── src/
│   └── main.py                     # SafeRouteFinder class (entry point)
├── safe_route_finder.py            # Core routing + safety scoring logic
├── read_lsoa_crime_data.py         # LSOA crime data processing
├── daylight_safety_info.py         # Sunrise/sunset & lighting scoring
├── visualization.py                # Route visualisation (interactive + static)
├── map_routes.py                   # Map plotting utilities
├── test_safe_route_camden.py       # Integration test (Camden area)
├── test_lsoa_lookup.py             # LSOA spatial lookup tests
├── requirements.txt
└── LICENSE
```

## Example Output

The tool generates a side-by-side comparison of the shortest route vs. safest route, with crime-density heatmap overlay and safety scores per segment.

## Roadmap

- [ ] Real-time crime data feed (Met Police API)
- [ ] Web frontend with Leaflet.js
- [ ] Expand beyond London (configurable city)
- [ ] Mobile-friendly PWA
- [ ] User-reported safety incidents

## License

MIT

## Author

Nineli Lashkarashvili
