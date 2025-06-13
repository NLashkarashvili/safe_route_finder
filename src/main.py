"""
Main entry point for the Safe Route Finder application.
"""
from typing import Dict, List, Tuple
from .data.data_loader import DataLoader
from .safety.safety_scorer import SafetyScorer
from .routing.route_finder import RouteFinder
from .visualization.route_visualizer import RouteVisualizer


class SafeRouteFinder:
    def __init__(self):
        self.data_loader = DataLoader()
        self.safety_scorer = SafetyScorer(self.data_loader)
        self.route_finder = RouteFinder(self.data_loader, self.safety_scorer)
        self.visualizer = RouteVisualizer()

    def find_route(self, start_point: Tuple[float, float],
                  end_point: Tuple[float, float],
                  visualize: bool = True) -> Dict[str, Dict]:
        """
        Find and optionally visualize safe routes between two points.

        Args:
            start_point: Tuple of (latitude, longitude) for start location
            end_point: Tuple of (latitude, longitude) for end location
            visualize: Whether to show route visualization

        Returns:
            Dictionary containing route information and analysis
        """
        # Find routes
        routes = self.route_finder.find_routes(start_point, end_point)

        # Load network for analysis
        G = self.data_loader.load_network(start_point)

        # Analyze routes
        analyses = {
            'shortest': self.route_finder.analyze_route(G, routes['shortest'], 'shortest'),
            'safest': self.route_finder.analyze_route(G, routes['safest'], 'safest')
        }

        # Visualize if requested
        if visualize:
            self.visualizer.visualize_routes(G, routes, analyses)

        return {
            'routes': routes,
            'analyses': analyses
        }


def main():
    """Example usage of the Safe Route Finder."""
    # Example coordinates (Camden Market to Camden Town tube station)
    start_point = (51.5415, -0.1468)
    end_point = (51.5390, -0.1426)

    finder = SafeRouteFinder()
    result = finder.find_route(start_point, end_point)

    # Print route analyses
    for route_type, analysis in result['analyses'].items():
        print(f"\n{route_type.title()} Route Analysis:")
        print(f"Total length: {analysis['total_length']:.0f}m")
        print(f"Average safety score: {analysis['average_safety_score']:.1f}/10")


if __name__ == '__main__':
    main()
