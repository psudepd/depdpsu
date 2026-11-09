"""Folium map renderer for the DEPD Sindh GIS page.

Design principles:
  * Real pins for facilities that submitted coordinates inside Sindh.
  * Real pins for facilities that submitted coordinates inside Pakistan but
    outside Sindh — flagged "Outside Sindh — please verify" so nothing is
    hidden.
  * District-centroid fallback pins (labelled "Missing location — district
    centroid shown") for facilities whose coordinates are missing or are
    outside Pakistan altogether.
  * Shaped + iconed markers per facility type (icon from gis_icon_map.csv).
  * Sized halo behind each marker, scaled by Direct beneficiaries.
  * OpenStreetMap basemap (no API key required, no watermark).
  * Rich HTML popup card with reach, gender, period, source, location status.
  * Tooltip format: "<service label> — <facility name>" (TEST prefix stripped).
"""
from __future__ import annotations

import math
import os
import re

import folium
import pandas as pd

from src.geo.map_styling import MapStyler

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(HERE, os.pardir, os.pardir))
OWNERSHIP_PATH = os.path.join(PROJECT_ROOT, "data", "ownership_by_type.csv")
ICON_MAP_PATH = os.path.join(PROJECT_ROOT, "docs", "gis_icon_map.csv")

# Two nested envelopes:
#  - SINDH_BBOX: the recognised Sindh extent (padded slightly).
#  - PAKISTAN_BBOX: the broad envelope around Pakistan. Coordinates inside
#    this but outside SINDH_BBOX are still pinned (flagged as outside Sindh).
SINDH_BBOX = (23.5, 66.0, 28.7, 71.6)        # min_lat, min_lon, max_lat, max_lon
PAKISTAN_BBOX = (23.0, 60.0, 37.5, 78.0)

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

DEFAULT_ICONS = {
    "rcmhc": "plus-square", "rcph": "plus-square",
    "gov_se": "school", "inclusive": "book",
    "deaf_reach": "school", "sipmr": "plus-square",
    "ipmr": "plus-square", "carts": "tools",
    "nowpdp": "briefcase", "hostel": "bed",
    "vtc": "tools", "academy": "graduation-cap",
    "gia": "hand-holding-heart",
    "sindh_persons_with_disabilitie": "id-card",
    "dis_cer": "id-card",
    "legal_support__beneficiaries": "balance-scale",
    "pcrdp": "id-card", "assistive_ip": "wheelchair",
    "regional_dir": "building",
}

# Human-readable labels for the facility types (used in tooltip "Service — Name")
SERVICE_LABELS = {
    "rcmhc": "RCMHC",
    "rcph": "RCPH",
    "gov_se": "Govt SE Centre",
    "inclusive": "Inclusive Education",
    "deaf_reach": "Deaf Reach",
    "sipmr": "SIPMR",
    "ipmr": "IPMR",
    "carts": "C-ARTS",
    "nowpdp": "NOWPDP",
    "hostel": "Hostel",
    "vtc": "VTC",
    "academy": "Academy",
    "gia": "GIA",
    "sindh_persons_with_disabilitie": "SPDPA",
    "dis_cer": "Disability Certificate",
    "legal_support__beneficiaries": "Legal Support",
    "pcrdp": "PCRDP",
    "assistive_ip": "Assistive Devices",
    "regional_dir": "Regional Directorate",
}

_FA_COLOR = {
    "#2E7D32": "green",
    "#1F5FBF": "blue",
    "#7B3FA0": "purple",
    "#6B7280": "gray",
}

FALLBACK_WARNING = (
    '<div style="padding:10px 12px;border:1px solid #1F5FBF;background:#eef3f8;'
    'color:#18345A;border-radius:6px;font-size:13px;">'
    '<b style="color:#1F5FBF;">Executive map</b> &middot; '
    'Pins shaped &amp; iconed by facility type &middot; '
    'Colour = ownership class &middot; '
    'Amber pins = district centroid fallback (no valid coordinates submitted).'
    '</div>'
)

SUBMITTED_COORDS_INFO = (
    "Coordinates are shown exactly as submitted when they fall inside "
    "Pakistan. Where a facility did not submit valid coordinates, or the "
    "coordinate lies outside Pakistan, its district centroid is shown and "
    "clearly labelled."
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _num(v):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if not math.isnan(x) else None


def _clean_name(raw) -> str:
    """Remove leading 'TEST' prefix (case-insensitive) and whitespace."""
    s = str(raw or "").strip()
    s = re.sub(r"^\s*test\s+", "", s, flags=re.IGNORECASE)
    return s.strip()


def _in_box(lat, lon, box) -> bool:
    if lat is None or lon is None:
        return False
    min_lat, min_lon, max_lat, max_lon = box
    return min_lat <= lat <= max_lat and min_lon <= lon <= max_lon


def _coords_in_sindh(lat, lon) -> bool:
    return _in_box(lat, lon, SINDH_BBOX)


def _coords_in_pakistan(lat, lon) -> bool:
    return _in_box(lat, lon, PAKISTAN_BBOX)


def _raw_lat_lon(row):
    """Return the submitted coordinate (lat, lon) as numbers, or (None, None)."""
    lat = _num(row.get("_GIS_latitude"))
    lon = _num(row.get("_GIS_longitude"))
    if lat is not None and lon is not None:
        return lat, lon
    gis = row.get("GIS")
    if gis is not None:
        try:
            parts = str(gis).split()
            if len(parts) >= 2:
                lat2 = _num(parts[0])
                lon2 = _num(parts[1])
                if lat2 is not None and lon2 is not None:
                    return lat2, lon2
        except (AttributeError, ValueError):
            pass
    return None, None


def _gis_lat_lon(row):
    """Return (lat, lon, source).

    source is one of:
      'form'                 coordinate inside Sindh
      'form_outside_sindh'   coordinate inside Pakistan but outside Sindh
      'district'             district centroid fallback (blank / outside Pakistan)
      None                   nothing usable
    """
    lat, lon = _raw_lat_lon(row)
    if lat is not None and lon is not None:
        if _coords_in_sindh(lat, lon):
            return lat, lon, "form"
        if _coords_in_pakistan(lat, lon):
            return lat, lon, "form_outside_sindh"
        # Outside Pakistan — fall through to district fallback.

    d = str(row.get("district", "")).strip().lower().replace(" ", "_")
    c = DISTRICT_CENTROIDS.get(d)
    if c is not None:
        return c[0], c[1], "district"

    return None, None, None


def _marker_radius(direct) -> int:
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


def _fa_colour(ownership_hex: str) -> str:
    if not ownership_hex:
        return "gray"
    return _FA_COLOR.get(str(ownership_hex).strip().upper(), "gray")


def _location_html(location_source: str) -> str:
    if location_source == "form":
        return '<span style="color:#16a34a;font-weight:600;">&#10003; Location verified (inside Sindh)</span>'
    if location_source == "form_outside_sindh":
        return ('<span style="color:#dc2626;font-weight:600;">'
                '&#9888; Outside Sindh — please verify</span>')
    if location_source == "district":
        return ('<span style="color:#d97706;font-weight:600;">'
                '&#9888; Missing location — district centroid shown</span>')
    return '<span style="color:#dc2626;font-weight:600;">&#10007; No location</span>'


def _tooltip_text(facility_type: str, facility_name) -> str:
    """Tooltip format: 'Service label — Facility name' (TEST prefix removed)."""
    label = SERVICE_LABELS.get(str(facility_type).strip(), str(facility_type).strip() or "Service")
    name = _clean_name(facility_name)
    if name:
        return f"{label} — {name}"
    return label


def _popup_html(row, location_source: str) -> str:
    ftype = str(row.get("facility_type") or "").strip()
    name = _clean_name(row.get("facility_name")) or "(no name)"
    ftype_label = SERVICE_LABELS.get(ftype, ftype or "(none)")
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
    loc_html = _location_html(location_source)

    return (
        '<div style="font-family:Segoe UI,Roboto,Arial,sans-serif;'
        'min-width:280px;max-width:340px;color:#18345A;background:#ffffff;'
        'padding:8px 6px;border-radius:6px;">'
        f'<div style="font-size:15px;font-weight:700;line-height:1.3;'
        f'margin-bottom:2px;color:#18345A;">{name}</div>'
        f'<div style="font-size:12px;color:#66758C;margin-bottom:8px;">'
        f'{ftype_label} &middot; {district} &middot; {division}</div>'
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
    m = folium.Map(location=[26.5, 68.5], zoom_start=7, tiles="OpenStreetMap")
    styler = _styler()

    markers: list = []
    fallback_rows: list = []
    missing_rows: list = []

    if df is not None and len(df):
        for _, row in df.iterrows():
            ftype = str(row.get("facility_type", "")).strip()
            style = styler.get_marker_style(ftype)
            fa_colour = _fa_colour(style["color"])

            icon_name = str(style.get("icon") or "").strip()
            if not icon_name or icon_name == "question":
                icon_name = DEFAULT_ICONS.get(ftype, "map-marker")
            icon_name = icon_name.lower().replace(" ", "-").replace("_", "-")

            lat, lon, loc_src = _gis_lat_lon(row)
            direct = row.get("direct")

            if lat is None or lon is None:
                missing_rows.append({
                    "facility_name": _clean_name(row.get("facility_name", "")),
                    "district": row.get("district", ""),
                    "reason": "no usable coordinates (and no district centroid)",
                })
                continue

            r = _marker_radius(direct)

            # Halo behind marker
            folium.CircleMarker(
                location=[lat, lon],
                radius=r + 6,
                color=style["color"],
                weight=0,
                fill=True,
                fill_color=style["color"],
                fill_opacity=0.18,
            ).add_to(m)

            # Shaped + iconed marker with "Service — Name" tooltip
            folium.Marker(
                location=[lat, lon],
                tooltip=_tooltip_text(ftype, row.get("facility_name", "")),
                popup=folium.Popup(_popup_html(row, loc_src), max_width=360),
                icon=folium.Icon(color=fa_colour, icon=icon_name, prefix="fa"),
            ).add_to(m)

            markers.append({
                "facility_name": _clean_name(row.get("facility_name", "")),
                "facility_type": ftype,
                "district": row.get("district", ""),
                "lat": lat,
                "lon": lon,
                "location_source": loc_src,
                "inside_sindh_bbox": _coords_in_sindh(lat, lon),
                "inside_pakistan_bbox": _coords_in_pakistan(lat, lon),
                "icon": icon_name,
                "colour": fa_colour,
            })

            if loc_src == "district":
                fallback_rows.append({
                    "facility_name": _clean_name(row.get("facility_name", "")),
                    "district": row.get("district", ""),
                    "reason": "district centroid shown (no valid coordinates submitted, or coordinate outside Pakistan)",
                })
            elif loc_src == "form_outside_sindh":
                fallback_rows.append({
                    "facility_name": _clean_name(row.get("facility_name", "")),
                    "district": row.get("district", ""),
                    "reason": "submitted coordinate is inside Pakistan but outside Sindh — please verify",
                })

    if markers:
        lats = [mk["lat"] for mk in markers]
        lons = [mk["lon"] for mk in markers]
        m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]], padding=[30, 30])

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