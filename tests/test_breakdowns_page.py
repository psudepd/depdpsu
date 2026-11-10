"""Reconciliation tests for the Breakdowns page (Phase 3C).

For three filter combinations, the Direct grand total must reconcile across
the service, division and district breakdown tables AND against
aggregate_reach() — within ±0.1.
"""
from src.kpi.aggregate import aggregate_reach, breakdown
from src.ui.state import get_filtered_dataframe

FILTERS = [
    {},
    {"division": "sukkur"},
    {"service_type": "gov_se"},
]


def _close(a, b, tol=0.1):
    return abs(a - b) <= tol


def test_breakdown_reconciles_no_filter():
    df = get_filtered_dataframe(basis="active")
    a = float(breakdown(df, "service")["direct"].sum())
    b = float(breakdown(df, "division")["direct"].sum())
    c = float(breakdown(df, "district")["direct"].sum())
    r = float(aggregate_reach(df)["direct"])
    assert _close(a, r), f"service {a} != reach {r}"
    assert _close(b, r), f"division {b} != reach {r}"
    assert _close(c, r), f"district {c} != reach {r}"


def test_breakdown_reconciles_division_filter():
    df = get_filtered_dataframe(basis="active", division="sukkur")
    a = float(breakdown(df, "service")["direct"].sum())
    b = float(breakdown(df, "division")["direct"].sum())
    c = float(breakdown(df, "district")["direct"].sum())
    r = float(aggregate_reach(df)["direct"])
    assert _close(a, r), f"service {a} != reach {r}"
    assert _close(b, r), f"division {b} != reach {r}"
    assert _close(c, r), f"district {c} != reach {r}"


def test_breakdown_reconciles_service_filter():
    df = get_filtered_dataframe(basis="active", service_type="gov_se")
    a = float(breakdown(df, "service")["direct"].sum())
    b = float(breakdown(df, "division")["direct"].sum())
    c = float(breakdown(df, "district")["direct"].sum())
    r = float(aggregate_reach(df)["direct"])
    assert _close(a, r), f"service {a} != reach {r}"
    assert _close(b, r), f"division {b} != reach {r}"
    assert _close(c, r), f"district {c} != reach {r}"


def test_breakdown_reconciles_cumulative_basis():
    df = get_filtered_dataframe(basis="cumulative")
    a = float(breakdown(df, "service")["direct"].sum())
    b = float(breakdown(df, "division")["direct"].sum())
    c = float(breakdown(df, "district")["direct"].sum())
    r = float(aggregate_reach(df)["direct"])
    assert _close(a, r), f"service {a} != reach {r}"
    assert _close(b, r), f"division {b} != reach {r}"
    assert _close(c, r), f"district {c} != reach {r}"


import os

import pandas as pd
from src.ui.pages.breakdowns import (
    _service_table,
    _region_table,
    _district_table,
)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FIXTURE = os.path.join(ROOT, "tests", "expected_sample_107_rows.csv")


def _df():
    return pd.read_csv(FIXTURE, dtype=object)


def test_service_table_reconciles():
    df = _df()
    tbl = _service_table(df)
    # exclude the regional_dir row from the total
    kept = tbl[~tbl["Service"].str.contains("regional_dir", case=False)]
    assert abs(float(kept["Direct"].sum()) - float(aggregate_reach(df)["direct"])) < 0.1


def test_region_table_has_six_rows():
    tbl = _region_table(_df())
    assert len(tbl) == 6


def test_district_table_has_thirty_rows():
    tbl = _district_table(_df())
    assert len(tbl) == 30
