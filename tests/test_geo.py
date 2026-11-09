"""Geo / GIS tests.

Behaviour under test (matches the current map policy):

  * Pins are placed at submitted coordinates when those are valid (inside
    the Sindh bounding box).
  * When submitted coordinates are missing or impossible, the pin is placed
    at the district centroid and clearly labelled
    (``location_source == "district"``). Every such row appears in
    ``_missing_rows`` with a human-readable reason.
  * Never a fake pin at a guessed facility location.
  * The static renderer must never invent polygons: it raises
    ``MissingBoundariesError`` when ``boundaries is None``.
  * The renderer strips a leading ``TEST`` prefix from facility names in
    markers and in ``_missing_rows``; these tests therefore key on the
    cleaned names.
"""
import os

import pandas as pd
import pytest

from src.geo.render_folium import build_folium_map

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.join(HERE, os.pardir, "data", "synthetic_submissions.csv")


def _df():
    return pd.read_csv(FIXTURE)


def _markers_by_name(m):
    """Return {facility_name: marker_record} for a folium map."""
    return {mk["facility_name"]: mk for mk in m._markers}


# ---------------------------------------------------------------------------
# Map surface — fallback shape
# ---------------------------------------------------------------------------

def test_fallback_map_returned_when_boundaries_missing():
    """build_folium_map returns a map object with _markers and _missing_rows."""
    m = build_folium_map(_df(), None)
    assert m is not None
    assert getattr(m, "_fallback", False) is True
    assert hasattr(m, "_markers")
    assert hasattr(m, "_missing_rows")


def test_fallback_markers_record_location_source_and_bbox():
    """Each marker carries location_source ('form' | 'district') and
    inside_sindh_bbox (bool), so the page can summarise coverage without
    recomputing geometry."""
    m = build_folium_map(_df(), None)
    assert len(m._markers) > 0
    for mk in m._markers:
        assert "location_source" in mk
        assert mk["location_source"] in {"form", "district", "form_outside_sindh"}
        assert "inside_sindh_bbox" in mk
        assert isinstance(mk["inside_sindh_bbox"], bool)


# ---------------------------------------------------------------------------
# Row 1001 — Karachi Central, valid coordinates
# ---------------------------------------------------------------------------

def test_row_1001_pinned_at_submitted_coordinates():
    """Row 1001 (Karachi 24.93, 67.07) is pinned at its submitted coords."""
    m = build_folium_map(_df(), None)
    markers = _markers_by_name(m)
    mk = markers.get("RCMHC Karachi Central")
    assert mk is not None, "row 1001 not pinned"
    assert mk["location_source"] == "form"
    assert 24.0 <= mk["lat"] <= 28.5
    assert 66.5 <= mk["lon"] <= 71.5
    # Not flagged as a fallback row.
    reasons = {str(r["facility_name"]): str(r["reason"])
               for _, r in m._missing_rows.iterrows()}
    assert "RCMHC Karachi Central" not in reasons


# ---------------------------------------------------------------------------
# Row 1019 — London coordinates, out of Sindh bbox
# ---------------------------------------------------------------------------

def test_row_1019_out_of_bbox_placed_at_district_centroid():
    """Row 1019 (London 51.5, -0.12) cannot be pinned at London. It is
    placed at its district centroid (Larkana) and clearly labelled."""
    m = build_folium_map(_df(), None)
    markers = _markers_by_name(m)
    mk = markers.get("RCPH Larkana")
    assert mk is not None, "row 1019 not pinned at all"
    assert mk["location_source"] == "district"
    assert 24.0 <= mk["lat"] <= 28.5
    assert 66.5 <= mk["lon"] <= 71.5

    # And it is listed in the missing-locations table with the fallback reason.
    reasons = {str(r["facility_name"]): str(r["reason"])
               for _, r in m._missing_rows.iterrows()}
    assert "RCPH Larkana" in reasons
    assert "district centroid" in reasons["RCPH Larkana"].lower()


# ---------------------------------------------------------------------------
# Row 1018 — blank coordinates
# ---------------------------------------------------------------------------

def test_row_1018_blank_coords_placed_at_district_centroid():
    """Row 1018 (blank GIS) has no usable coordinates. It is placed at its
    district centroid (Mirpurkhas) and clearly labelled, not skipped."""
    m = build_folium_map(_df(), None)
    markers = _markers_by_name(m)
    mk = markers.get("Hostel Mirpurkhas Annex")
    assert mk is not None, "row 1018 not pinned at all"
    assert mk["location_source"] == "district"

    reasons = {str(r["facility_name"]): str(r["reason"])
               for _, r in m._missing_rows.iterrows()}
    assert "Hostel Mirpurkhas Annex" in reasons
    assert "district centroid" in reasons["Hostel Mirpurkhas Annex"].lower()


# ---------------------------------------------------------------------------
# TEST prefix is stripped from names in both markers and the fallback table
# ---------------------------------------------------------------------------

def test_test_prefix_is_stripped_from_names():
    """No marker or missing-row name should start with 'TEST '."""
    m = build_folium_map(_df(), None)
    for mk in m._markers:
        assert not str(mk["facility_name"]).upper().startswith("TEST "), mk
    for _, r in m._missing_rows.iterrows():
        assert not str(r["facility_name"]).upper().startswith("TEST "), r


# ---------------------------------------------------------------------------
# Static renderer must never invent polygons
# ---------------------------------------------------------------------------

def test_static_raises_when_boundaries_missing():
    """The static JPG renderer must raise MissingBoundariesError when
    boundaries is None."""
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