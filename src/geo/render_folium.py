"""Folium map renderer for the DEPD Sindh GIS page.

Design principle: the map is a READ-ONLY MIRROR of what facilities
submitted. Pins are placed at the coordinates entered in the Kobo form,
regardless of whether those coordinates are inside the Sindh bounding box.
Coordinate validation belongs in the Kobo form and the Data Quality page,
not in the map.

Marker colour comes from data/ownership_by_type.csv (via MapStyler or
docs/gis_icon_map.csv); icon from docs/gis_icon_map.csv.
"""
from __future__ import annotations

import math
import os

import folium
import pandas as pd
from shapely.geometry import Point, shape
from shapely.geometry.base import BaseGeometry

from src.geo.map_styling import MapStyler

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(HERE, os.pardir, os.pardir))
OWNERSHIP_PATH = os.path.join(PROJECT_ROOT, "data", "ownership_by_type.csv")
ICON_MAP_PATH = os.path.join(PROJECT_ROOT, "docs", "gis_icon_map.csv")

SINDH_BBOX = (24.0, 66.5, 28.5, 71.5)  # min_lat, min_lon, max_lat, max_lon

_FOLIUM_COLOR_ALIAS = {
    "#2E7D32": "darkgreen",
    "#1F5FBF": "darkblue",
    "#7B3FA0": "purple",
    "#6B7280": "gray",
}


def _folium_color(hex_or_name: str) -> str:
    if not hex_or_name:
        return "cadetblue"
    s = str(hex_or_name).strip()
    if s.startswith("#"):
        return _FOLIUM_COLOR_ALIAS.get(s.upper(), "cadetblue")
    return s if s in set(_FOLIUM_COLOR_ALIAS.values()) else "cadetblue"


def _icon_styles() -> dict:
    icon_df = pd.read_csv(ICON_MAP_PATH)
    styles: dict = {}
    for _, r in icon_df.iterrows():
        ftype = str(r["facility_type"]).strip()
        styles[ftype] = {
            "color": str(r["colour_hex"]).strip(),
            "shape": str(r["marker_shape"]).strip(),
            "icon": str(r["suggested_icon_name"]).strip(),
        }
    return styles


_ICON_STYLES = _icon_styles()


def _icon_style(ftype: str) -> dict:
    return _ICON_STYLES.get(
        ftype, {"color": "#6B7280", "shape": "circle", "icon": "question"}
    )


def _num(v):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if not math.isnan(x) else None


def _gis_lat_lon(row):
    lat = _num(row.get("_GIS_latitude"))
    lon = _num(row.get("_GIS_longitude"))
    if lat is not None and lon is not None:
        return lat, lon
    gis = row.get("GIS")
    if gis is None:
        return None, None
    try:
        parts = str(gis).split()
        if len(parts) >= 2:
            lat = _num(parts[0])
            lon = _num(parts[1])
            if lat is not None and lon is not None:
                return lat, lon
    except (AttributeError, ValueError):
        pass
    return None, None


def _coords_valid(lat: float, lon: float) -> bool:
    if lat is None or lon is None:
        return False
    min_lat, min_lon, max_lat, max_lon = SINDH_BBOX
    return min_lat <= lat <= max_lat and min_lon <= lon <= max_lon


def _point_in_district(lat: float, lon: float, district: str, district_polys: dict) -> bool:
    poly = district_polys.get(district)
    if poly is None or not isinstance(poly, BaseGeometry):
        return True
    return poly.contains(Point(lon, lat))


def _styler():
    return MapStyler(OWNERSHIP_PATH, ICON_MAP_PATH)


FALLBACK_WARNING = (
    '<div style="padding:12px;border:1px solid #b00020;background:#fdecea;color:#660000;">'
    "<b>District boundaries not loaded.</b> "
    "Pins show the coordinates entered in the Kobo form. Data validation "
    "happens in the form and the Data Quality page, not in this dashboard.</div>"
)

SUBMITTED_COORDS_INFO = (
    "Coordinates are shown exactly as submitted. Data validation is handled "
    "in the Kobo form and the Data Quality page, not in this dashboard."
)


def _fallback_map(df: pd.DataFrame):
    m = folium.Map(location=[26.5, 68.5], zoom_start=6, tiles="OpenStreetMap")
    markers = []
    no_coords_rows = []
    if df is not None and len(df):
        for _, row in df.iterrows():
            ftype = str(row.get("facility_type", "")).strip()
            style = _icon_style(ftype)
            lat, lon = _gis_lat_lon(row)
            district = row.get("district")

            if lat is None or lon is None:
                no_coords_rows.append(
                    {
                        "facility_name": row.get("facility_name", ""),
                        "district": district,
                        "reason": "no coordinates",
                    }
                )
                continue

            popup = (
                f"<b>{row.get('facility_name','')}</b><br>"
                f"Type: {ftype}<br>"
                f"District: {row.get('district','')}<br>"
                f"Direct: {row.get('direct','')}<br>"
                f"Lat/Lon: {lat:.4f}, {lon:.4f}"
            )
            folium.Marker(
                location=[lat, lon],
                popup=popup,
                tooltip=str(row.get("facility_name", "")),
                icon=folium.Icon(
                    color=_folium_color(style["color"]),
                    icon=style["icon"],
                    prefix="fa",
                ),
            ).add_to(m)
            markers.append(
                {
                    "facility_name": row.get("facility_name", ""),
                    "facility_type": ftype,
                    "district": district,
                    "lat": lat,
                    "lon": lon,
                    "inside_sindh_bbox": _coords_valid(lat, lon),
                }
            )
    m._fallback = True
    m._markers = markers
    m._missing_rows = (
        pd.DataFrame(no_coords_rows, columns=["facility_name", "district", "reason"])
        if no_coords_rows
        else pd.DataFrame(columns=["facility_name", "district", "reason"])
    )
    m._warning_html = FALLBACK_WARNING
    m._info_html = SUBMITTED_COORDS_INFO
    return m


def build_folium_map(df: pd.DataFrame, boundaries: dict | None):
    if boundaries is None:
        return _fallback_map(df)

    district_polys: dict = {}
    for feature in boundaries.get("features", []):
        props = feature.get("properties", {}) or {}
        name = (
            props.get("district_name")
            or props.get("name")
            or props.get("DISTRICT")
            or props.get("district")
            or props.get("shapeName")
        )
        geom = feature.get("geometry")
        if name is not None and geom is not None:
            district_polys[str(name).strip()] = shape(geom)

    styler = _styler()

    m = folium.Map(location=[26.5, 68.5], zoom_start=7, tiles="CartoDB positron")

    for feature in boundaries.get("features", []):
        props = feature.get("properties", {}) or {}
        name = (
            props.get("district_name")
            or props.get("name")
            or props.get("DISTRICT")
            or props.get("district")
            or props.get("shapeName")
        )
        geom = feature.get("geometry")
        if name is None or geom is None:
            continue
        folium.GeoJson(
            feature,
            style_function=lambda f: {
                "fillColor": "#EEF1F4",
                "color": "#E3E8ED",
                "weight": 1,
                "fillOpacity": 0.6,
            },
            tooltip=str(name),
        ).add_to(m)

    no_coords_rows = []
    if df is not None and len(df):
        for _, row in df.iterrows():
            ftype = str(row.get("facility_type", "")).strip()
            style = styler.get_marker_style(ftype)
            lat, lon = _gis_lat_lon(row)

            if lat is None or lon is None:
                no_coords_rows.append(
                    {
                        "facility_name": row.get("facility_name", ""),
                        "district": row.get("district"),
                        "reason": "no coordinates",
                    }
                )
                continue

            popup = (
                f"<b>{row.get('facility_name','')}</b><br>"
                f"Type: {ftype}<br>"
                f"District: {row.get('district','')}<br>"
                f"Direct: {row.get('direct','')}<br>"
                f"Lat/Lon: {lat:.4f}, {lon:.4f}"
            )
            folium.Marker(
                location=[lat, lon],
                popup=popup,
                tooltip=str(row.get("facility_name", "")),
                icon=folium.Icon(
                    color=_folium_color(style["color"]),
                    icon=style["icon"],
                    prefix="fa",
                ),
            ).add_to(m)

    m._missing_rows = (
        pd.DataFrame(no_coords_rows, columns=["facility_name", "district", "reason"])
        if no_coords_rows
        else pd.DataFrame(columns=["facility_name", "district", "reason"])
    )
    m._info_html = SUBMITTED_COORDS_INFO
    return m


def missing_boundaries_html() -> str:
    return (
        '<div style="padding:12px;border:1px solid #b00020;background:#fdecea;color:#660000;">'
        "<b>District boundary GeoJSON missing.</b> "
        "Download the Pakistan subnational administrative boundaries from HDX and place it at "
        "<code>data/boundaries/sindh_districts.geojson</code>. "
        "Table view shown instead.</div>"
    )