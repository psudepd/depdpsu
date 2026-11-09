"""Geo / GIS tests.

Behaviour under test (matches the chosen map policy):
- The map is a READ-ONLY MIRROR of submitted coordinates.
- Every row with numeric lat/lon is pinned, regardless of bbox.
- Rows with blank lat/lon are NOT pinned and are listed in the
  "Submissions without coordinates" table.
- When boundaries are absent, the map falls back (no polygons,
  no bbox filtering) instead of inventing polygons.
- The static renderer must never invent polygons.
"""
import os

import pandas as pd
import pytest

from src.geo.render_folium import build_folium_map

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.join(HERE, os.pardir, "data", "synthetic_submissions.csv")


def _df():
    return pd.read_csv(FIXTURE)


# ---------------------------------------------------------------------------
# Map pins — fallback (no boundaries file present)
# ---------------------------------------------------------------------------

def test_fallback_map_returned_when_boundaries_missing():
    """build_folium_map returns a map object with _markers and _missing_rows."""
    m = build_folium_map(_df(), None)
    assert m is not None
    assert getattr(m, "_fallback", False) is True
    assert hasattr(m, "_markers")
    assert hasattr(m, "_missing_rows")


def test_fallback_pins_in_bbox_row():
    """Row 1001 (Karachi 24.93, 67.07) is pinned."""
    m = build_folium_map(_df(), None)
    names = {mk["facility_name"] for mk in m._markers}
    assert "TEST RCMHC Karachi Central" in names


def test_fallback_pins_out_of_bbox_row():
    """Row 1019 (London 51.5, -0.12) is ALSO pinned — the map mirrors
    submitted coordinates. It is not filtered out and it is not listed
    in the 'missing' table."""
    m = build_folium_map(_df(), None)
    names = {mk["facility_name"] for mk in m._markers}
    assert "TEST RCPH Larkana" in names

    tbl = m._missing_rows
    table_names = {str(r["facility_name"]) for _, r in tbl.iterrows()}
    assert "TEST RCPH Larkana" not in table_names


def test_fallback_skips_blank_coords_row():
    """Row 1018 (blank GIS) is NOT pinned and IS listed in the
    'Submissions without coordinates' table with reason 'no coordinates'."""
    m = build_folium_map(_df(), None)
    names = {mk["facility_name"] for mk in m._markers}
    assert "TEST Hostel Mirpurkhas Annex" not in names

    tbl = m._missing_rows
    reasons = {str(r["facility_name"]): str(r["reason"]) for _, r in tbl.iterrows()}
    assert reasons.get("TEST Hostel Mirpurkhas Annex") == "no coordinates"


def test_fallback_markers_record_bbox_flag():
    """Each marker carries inside_sindh_bbox (True/False) so the page can
    show a count of out-of-bbox pins without removing them."""
    m = build_folium_map(_df(), None)
    assert len(m._markers) > 0
    for mk in m._markers:
        assert "inside_sindh_bbox" in mk
        assert isinstance(mk["inside_sindh_bbox"], bool)


# ---------------------------------------------------------------------------
# Static renderer must never invent polygons
# ---------------------------------------------------------------------------

def test_static_raises_when_boundaries_missing():
    """The static JPG renderer must raise MissingBoundariesError when
    boundaries is None. Uses whichever public name render_static.py exposes."""
    from src.geo import render_static as rs

    render_fn = (
        getattr(rs, "render_static_jpg", None)
        or getattr(rs, "render_static_map", None)
        or getattr(rs, "render", None)
    )
    assert render_fn is not None, (
        "render_static.py exposes none of: render_static_jpg, "
        "render_static_map, render. Check the file."
    )
    exc = getattr(rs, "MissingBoundariesError", None)
    assert exc is not None, "MissingBoundariesError not found in render_static.py"

    with pytest.raises(exc):
        try:
            render_fn(None)
        except TypeError:
            render_fn(_df(), None)