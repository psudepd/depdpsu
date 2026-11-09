"""Folium map renderer for the DEPD Sindh GIS page.

Design principles:
  * Real pins for facilities that submitted valid coordinates inside Sindh.
  * District-centroid fallback pins (labelled "Missing location — district
    centroid shown") for facilities whose coordinates are missing or
    impossible. Never a fake pin at a guessed facility location.
  * Pins sized by Direct beneficiaries, with a soft halo.
  * OpenStreetMap basemap (no API key required, no watermark).
  * Rich HTML popup card: name, type, district, division, Direct,
    Estimated family (x5), Estimated total, gender, period, source, flags,
    and an explicit location-verification line.

Boundary policy (interim): district polygon layers are deferred until a
licensed ADM2 file is available. This module always renders pin-only.
"""
from __future__ import annotations

import math
import os

import folium
import pandas as pd

from src.geo.map_styling import MapStyler

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(HERE, os.pardir, os.pardir))
OWNERSHIP_PATH = os.path.join(PROJECT_ROOT, "data", "ownership_by_type.csv")
ICON_MAP_PATH = os.path.join(PROJECT_ROOT, "docs", "gis_icon_map.csv")

SINDH_BBOX = (24.0, 66.5, 28.5, 71.5)  # min_lat, min_lon, max_lat, max_lon

# Approximate district centroids for facilities whose submitted coordinates
# are missing or invalid. Used ONLY as a clearly labelled fallback.
DISTRICT_CENTROIDS = {
    "badin": (24.6595, 68.8361),
    "dadu": (26.7304, 67.7668),
    "ghotki": (28.0118, 69.3103),
    "hyderabad": (25.3792, 68.3436),
    "jacobabad": (28.2774, 68.4433),
    "jamshoro": (25.4137, 68.2734),
    "kamber_shahdadkot": (27.8505, 67.9057),
    "karachi_central": (24.9440, 67.0806),
    "karachi_east": (24.9173, 67.1335),
    "karachi_south": (24.9260, 67.1386),
    "karachi_west": (24.9804, 66.9914),
    "keamari": (24.9030, 67.0100),
    "khairpur": (27.5356, 68.7320),
    "korangi": (24.8140, 67.1320),
    "larkana": (27.5580, 68.1947),
    "malir": (24.8697, 67.3603),
    "matiari": (25.8136, 68.4168),
    "mirpurkhas": (25.4549, 68.6745),
    "naushahro_feroze": (26.8293, 68.1438),
    "sanghar": (26.0445, 68.9482),
    "shaheed_benazirabad": (26.2330, 68.4167),
    "shikarpur": (27.9632, 68.6409),
    "sukkur": (27.7181, 68.8260),
    "tando_allahyar": (25.4581, 68.7228),
    "tando_muhammad_khan": (25.1356, 68.5178),
    "thatta": (24.7473, 67.8923),
    "umerkot": (25.3595, 69.7385),
}

_FOLIUM_COLOR_ALIAS = {
    "#2E7D32": "darkgreen",
    "#1F5FBF": "darkblue",
    "#7B3FA0": "purple",
    "#6B7280": "gray",
}

FALLBACK_WARNING = (
    '<div style="padding:10px 12px;border:1px solid #1F5FBF;background:#eef3f8;'
    'color:#18345A;border-radius:6px;font-size:13px;">'
    '<b style="color:#1F5FBF;">Executive map</b> &middot; '
    'Pins sized by Direct beneficiaries &middot; Colour = ownership class &middot; '
    'Amber pins = district centroid (facility did not submit valid coordinates).'
    '</div>'
)

SUBMITTED_COORDS_INFO = (
    "Coordinates are shown exactly as submitted. Where a facility did not "
    "submit valid coordinates, its district centroid is shown and clearly "
    "labelled. Validation happens in the Kobo form and the Data Quality page."
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _folium_color(hex_or_name: str) -> str:
    if not hex_or_name:
        return "cadetblue"
    s = str(hex_or_name).strip()
    if s.startswith("#"):
        return _FOLIUM_COLOR_ALIAS.get(s.upper(), "cadetblue")
    return s if s in set(_FOLIUM_COLOR_ALIAS.values()) else "cadetblue"


def _num(v):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if not math.isnan(x) else None


def _coords_in_sindh(lat, lon) -> bool:
    if lat is None or lon is None:
        return False
    min_lat, min_lon, max_lat, max_lon = SINDH_BBOX
    return min_lat <= lat <= max_lat and min_lon <= lon <= max_lon


def _gis_lat_lon(row):
    """Return (lat, lon, source) where source is 'form' | 'district' | None."""
    lat = _num(row.get("_GIS_latitude"))
    lon = _num(row.get("_GIS_longitude"))
    if lat is not None and lon is not None and _coords_in_sindh(lat, lon):
        return lat, lon, "form"

    gis = row.get("GIS")
    if gis is not None:
        try:
            parts = str(gis).split()
            if len(parts) >= 2:
                lat2 = _num(parts[0])
                lon2 = _num(parts[1])
                if lat2 is not None and lon2 is not None and _coords_in_sindh(lat2, lon2):
                    return lat2, lon2, "form"
        except (AttributeError, ValueError):
            pass

    d = str(row.get("district", "")).strip().lower().replace(" ", "_")
    c = DISTRICT_CENTROIDS.get(d)
    if c is not None:
        return c[0], c[1], "district"

    return None, None, None


def _marker_radius(direct) -> int:
    """Pin size from Direct beneficiaries, clamped to [6, 22]."""
    try:
        v = float(direct or 0)
    except (TypeError, ValueError):
        v = 0
    if v <= 0:
        return 6
    return int(max(6, min(22, math.sqrt(v) * 1.3)))


def _fmt(v) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "&mdash;"
    try:
        return f"{int(round(float(v))):,}"
    except (TypeError, ValueError):
        return "&mdash;"


def _popup_html(row, location_source: str) -> str:
    name = str(row.get("facility_name") or "(no name)")
    ftype = str(row.get("facility_type") or "(none)")
    district = str(row.get("district") or "&mdash;")
    division = str(row.get("division_mapped") or row.get("division") or "&mdash;")
    period = str(row.get("rp_end") or "&mdash;")
    direct = _fmt(row.get("direct"))
    family = _fmt(row.get("family"))
    total = _fmt(row.get("total_reach"))
    src = str(row.get("source") or "&mdash;")
    flags = str(row.get("flags") or "&mdash;")
    male = _fmt(row.get("w_male"))
    female = _fmt(row.get("w_female"))
    trans = _fmt(row.get("w_trans"))

    if location_source == "form":
        loc_html = '<span style="color:#16a34a;font-weight:600;">&#10003; Location verified</span>'
    elif location_source == "district":
        loc_html = ('<span style="color:#d97706;font-weight:600;">'
                    '&#9888; Missing location &mdash; district centroid shown</span>')
    else:
        loc_html = '<span style="color:#dc2626;font-weight:600;">&#10007; No location</span>'

    return (
        '<div style="font-family:Segoe UI,Roboto,Arial,sans-serif;'
        'min-width:280px;max-width:340px;color:#18345A;background:#ffffff;'
        'padding:8px 6px;border-radius:6px;">'
        f'<div style="font-size:15px;font-weight:700;line-height:1.3;'
        f'margin-bottom:2px;color:#18345A;">{name}</div>'
        f'<div style="font-size:12px;color:#66758C;margin-bottom:8px;">'
        f'{ftype} &middot; {district} &middot; {division}</div>'
        f'<div style="font-size:11px;margin-bottom:10px;">{loc_html}</div>'
        '<table style="width:100%;font-size:12px;border-collapse:collapse;">'
        f'<tr><td style="color:#66758C;padding:2px 0;">Direct</td>'
        f'<td style="text-align:right;font-weight:600;color:#18345A;">{direct}</td></tr>'
        f'<tr><td style="color:#66758C;padding:2px 0;">Estimated family (x5)</td>'
        f'<td style="text-align:right;font-weight:600;color:#18345A;">{family}</td></tr>'
        f'<tr><td style="color:#66758C;padding:2px 0;">Estimated total reach</td>'
        f'<td style="text-align:right;font-weight:600;color:#18345A;">{total}</td></tr>'
        f'<tr><td style="color:#66758C;padding:2px 0;">Male / Female / Trans</td>'
        f'<td style="text-align:right;color:#18345A;">{male} / {female} / {trans}</td></tr>'
        '</table>'
        '<div style="border-top:1px solid #EEF3F8;margin:8px 0 0 0;'
        'padding-top:6px;font-size:11px;color:#66758C;line-height:1.6;">'
        f'Period: {period}<br/>Source: {src}<br/>Flags: {flags}'
        '</div>'
        '</div>'
    )


def _styler() -> MapStyler:
    return MapStyler(OWNERSHIP_PATH, ICON_MAP_PATH)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_folium_map(df: pd.DataFrame, boundaries: dict | None = None):
    """Always renders the pin-only map (district polygon layers deferred).

    Returns a folium.Map with attributes:
      _markers       list of dicts (name, type, district, lat, lon, source)
      _missing_rows  pd.DataFrame of facilities shown at district centroid
      _warning_html  banner HTML
      _info_html     info-line HTML
    """
    m = folium.Map(location=[26.5, 68.5], zoom_start=7, tiles="OpenStreetMap")
    styler = _styler()

    markers: list = []
    fallback_rows: list = []
    missing_rows: list = []

    if df is not None and len(df):
        for _, row in df.iterrows():
            ftype = str(row.get("facility_type", "")).strip()
            style = styler.get_marker_style(ftype)
            color = _folium_color(style["color"])
            lat, lon, loc_src = _gis_lat_lon(row)
            direct = row.get("direct")

            if lat is None or lon is None:
                missing_rows.append({
                    "facility_name": row.get("facility_name", ""),
                    "district": row.get("district", ""),
                    "reason": "no usable coordinates (and no district centroid)",
                })
                continue

            r = _marker_radius(direct)

            # Halo glow underneath
            folium.CircleMarker(
                location=[lat, lon],
                radius=r + 5,
                color=color,
                weight=0,
                fill=True,
                fill_color=color,
                fill_opacity=0.18,
            ).add_to(m)

            # Main pin
            folium.CircleMarker(
                location=[lat, lon],
                radius=r,
                color="#18345A",
                weight=1,
                fill=True,
                fill_color=color,
                fill_opacity=0.92,
                tooltip=str(row.get("facility_name", "")),
                popup=folium.Popup(_popup_html(row, loc_src), max_width=360),
            ).add_to(m)

            marker_rec = {
                "facility_name": row.get("facility_name", ""),
                "facility_type": ftype,
                "district": row.get("district", ""),
                "lat": lat,
                "lon": lon,
                "location_source": loc_src,
                "inside_sindh_bbox": _coords_in_sindh(lat, lon),
            }
            markers.append(marker_rec)

            if loc_src == "district":
                fallback_rows.append({
                    "facility_name": row.get("facility_name", ""),
                    "district": row.get("district", ""),
                    "reason": "district centroid shown (no valid coordinates submitted)",
                })

    if markers:
        lats = [mk["lat"] for mk in markers]
        lons = [mk["lon"] for mk in markers]
        m.fit_bounds(
            [[min(lats), min(lons)], [max(lats), max(lons)]],
            padding=[30, 30],
        )

    m._markers = markers
    m._fallback = True
    m._missing_rows = (
        pd.DataFrame(fallback_rows + missing_rows,
                     columns=["facility_name", "district", "reason"])
        if (fallback_rows or missing_rows)
        else pd.DataFrame(columns=["facility_name", "district", "reason"])
    )
    m._warning_html = FALLBACK_WARNING
    m._info_html = SUBMITTED_COORDS_INFO
    return m


def missing_boundaries_html() -> str:
    return (
        '<div style="padding:10px 12px;border:1px solid #1F5FBF;background:#eef3f8;'
        'color:#18345A;border-radius:6px;font-size:13px;">'
        '<b style="color:#1F5FBF;">District polygon layers not enabled.</b> '
        'Facility pins are shown on OpenStreetMap. District boundaries will be '
        'added when a licensed ADM2 file is available.</div>'
    )