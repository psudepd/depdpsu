"""
GIS Map Styling Module

This module handles the styling of GIS map markers based on ownership and service type.
Rules are defined in `docs/gis_map_styling.md` and `docs/gis_icon_map.csv`.

Colour, shape and icon all come from ``gis_icon_map.csv``. ``ownership_by_type.csv``
carries the ownership class per facility type; the map uses it only as a check
(and to classify a facility as "office only" for regional_dir).
"""
import pandas as pd


class MapStyler:
    """
    Handles the styling of GIS map markers.
    """

    def __init__(self, ownership_path: str, icon_map_path: str):
        """
        Initialize the MapStyler with ownership and icon mapping data.

        Args:
            ownership_path (str): Path to the ownership_by_type.csv file.
            icon_map_path (str): Path to the gis_icon_map.csv file.
        """
        self.ownership_df = pd.read_csv(ownership_path)
        self.icon_map_df = pd.read_csv(icon_map_path)

    def get_marker_style(self, facility_type: str) -> dict:
        """
        Get the marker style (color, shape, icon) for a given facility type.

        Args:
            facility_type (str): The type of the facility.

        Returns:
            dict: A dictionary containing 'color', 'shape', and 'icon' keys.
        """
        # Colour, shape and icon all live in gis_icon_map.csv.
        icon_info = self.icon_map_df[self.icon_map_df['facility_type'] == facility_type]
        if icon_info.empty:
            return {
                "color": "#6B7280",   # grey for unknown types
                "shape": "circle",
                "icon": "question",
            }

        return {
            "color": icon_info['colour_hex'].values[0],
            "shape": icon_info['marker_shape'].values[0],
            "icon": icon_info['suggested_icon_name'].values[0],
        }