"""Regression tests for src/geo/map_styling.py.

The original implementation read `colour_hex` from ownership_by_type.csv,
which does not have that column — a KeyError that only surfaced the first
time the map page ran with real boundaries loaded.
"""
import os

import pandas as pd
import pytest

from src.geo.map_styling import MapStyler

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
OWNERSHIP = os.path.join(ROOT, "data", "ownership_by_type.csv")
ICONS = os.path.join(ROOT, "docs", "gis_icon_map.csv")


@pytest.fixture(scope="module")
def styler():
    return MapStyler(OWNERSHIP, ICONS)


def test_returns_full_style_for_known_types(styler):
    for ftype in ["rcmhc", "gov_se", "nowpdp", "assistive_ip", "carts",
                  "deaf_reach", "regional_dir"]:
        style = styler.get_marker_style(ftype)
        assert set(style.keys()) == {"color", "shape", "icon"}
        assert style["color"].startswith("#")
        assert style["shape"]
        assert style["icon"]


def test_unknown_type_gets_grey_fallback(styler):
    style = styler.get_marker_style("this_type_does_not_exist")
    assert style == {"color": "#6B7280", "shape": "circle", "icon": "question"}


def test_every_facility_type_resolves_without_raising():
    choices = pd.read_csv(os.path.join(ROOT, "data", "choices.csv"))
    types = choices[choices["list_name"] == "facility_types"]["name"].dropna().tolist()
    s = MapStyler(OWNERSHIP, ICONS)
    for t in types:
        style = s.get_marker_style(t)
        assert style["color"]