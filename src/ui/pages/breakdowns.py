"""Breakdowns page (Phase 3C).

Three reconciliation tables — by service type (as filed), by division
(from the district mapping, never the submitted division), and by district
— each following the Active/Cumulative toggle. All three reconcile to the
same grand total as aggregate_reach().

The pure-pandas helpers (_service_table, _region_table, _district_table)
return DataFrames without Streamlit calls; render() displays them and adds
the grand total row plus downloads.
"""
from __future__ import annotations

import os

import pandas as pd
import streamlit as st

from src.kpi.aggregate import aggregate_reach, breakdown
from src.ui.components import table_with_downloads
from src.ui.service_cards import SERVICE_ORDER

FAMILY_FACTOR = int(os.environ.get("FAMILY_FACTOR", "5"))

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))
DIVISIONS_PATH = os.path.join(_REPO_ROOT, "data", "divisions.csv")
DISTRICT_DIVISION_PATH = os.path.join(_REPO_ROOT, "data", "district_division.csv")

NUMERIC_COLS = ["Reports", "Direct", "New", "Waiting"]


def _warn_invalid_cumulative(df: pd.DataFrame) -> None:
    """Surface rows the resolver rejected as implausible cumulative values."""
    if "source" not in df.columns:
        return
    invalid = df[df["source"].astype(str) == "invalid_value"]
    if len(invalid):
        services = ", ".join(sorted(invalid["facility_type"].astype(str).unique()))
        st.warning(
            f"{len(invalid)} submission(s) excluded from cumulative totals: "
            f"implausible value(s) for {services}. "
            "Please review the source data in Kobo."
        )


def _division_names() -> list[str]:
    """All 6 division names, sorted alphabetically."""
    dv = pd.read_csv(DIVISIONS_PATH, dtype=object)
    return sorted(dv["division_name"].dropna().astype(str).str.strip().tolist())


def _district_names():
    """(code -> name map, all 30 district names sorted alphabetically)."""
    dd = pd.read_csv(DISTRICT_DIVISION_PATH, dtype=object)
    code_to_name = {
        str(r["district_code"]).strip(): str(r["district_name"]).strip()
        for _, r in dd.iterrows()
    }
    return code_to_name, sorted(code_to_name.values())


def _enrich(base: pd.DataFrame, key_col: str) -> pd.DataFrame:
    """Add Indirect / Total reach / Share of Direct / Status columns."""
    base = base.copy()
    base["Indirect (Estimated)"] = base["Direct"] * FAMILY_FACTOR
    base["Total reach (Estimated)"] = base["Direct"] * (1 + FAMILY_FACTOR)
    total = float(base["Direct"].sum())
    if total > 0:
        base["Share of Direct (%)"] = base["Direct"] / total * 100.0
    else:
        base["Share of Direct (%)"] = 0.0
    base["Status"] = base["Reports"].apply(
        lambda r: "No reports" if r == 0 else "Updated"
    )
    return base


def _with_grand_total(tbl: pd.DataFrame, key_col: str, label: str = "Grand total"):
    """Append a grand total row whose Direct equals the table Direct sum."""
    total_direct = float(tbl["Direct"].sum())
    gt = {
        key_col: label,
        "Status": "",
        "Reports": int(tbl["Reports"].sum()),
        "Direct": total_direct,
        "Indirect (Estimated)": total_direct * FAMILY_FACTOR,
        "Total reach (Estimated)": total_direct * (1 + FAMILY_FACTOR),
        "New": float(tbl["New"].sum()),
        "Waiting": float(tbl["Waiting"].sum()),
        "Share of Direct (%)": 100.0 if total_direct > 0 else 0.0,
    }
    return pd.concat([tbl, pd.DataFrame([gt])], ignore_index=True)


def _service_table(df: pd.DataFrame) -> pd.DataFrame:
    """By service (as filed): one row per service plus a regional_dir row.

    regional_dir is office information only: its Direct is 0 and it is not
    added to any total. No grand total row here — render() appends it.
    """
    base = breakdown(df, "service")
    if len(base):
        base = base.rename(
            columns={
                "group": "Service",
                "reports": "Reports",
                "direct": "Direct",
                "new": "New",
                "waiting": "Waiting",
            }
        )
    else:
        base = pd.DataFrame(
            columns=["Service", "Reports", "Direct", "New", "Waiting"]
        )
    all_services = [code for _, codes in SERVICE_ORDER for code in codes]
    base = base.set_index("Service").reindex(all_services).reset_index()
    base["Service"] = base["Service"].astype(str)
    for c in NUMERIC_COLS:
        base[c] = pd.to_numeric(base[c], errors="coerce").fillna(0.0)
    base = _enrich(base, "Service")
    # regional_dir row: office information only, Direct = 0, not counted.
    regional = pd.DataFrame(
        [
            {
                "Service": "regional_dir (office information, not a service, not counted)",
                "Reports": 0,
                "Direct": 0.0,
                "Indirect (Estimated)": 0.0,
                "Total reach (Estimated)": 0.0,
                "New": 0.0,
                "Waiting": 0.0,
                "Share of Direct (%)": 0.0,
                "Status": "No reports",
            }
        ]
    )
    return pd.concat([base, regional], ignore_index=True)


def _region_table(df: pd.DataFrame) -> pd.DataFrame:
    """By region (division): always all 6 divisions, sorted alphabetically."""
    base = breakdown(df, "division")
    if len(base):
        base = base.rename(
            columns={
                "group": "Division",
                "reports": "Reports",
                "direct": "Direct",
                "new": "New",
                "waiting": "Waiting",
            }
        )
    else:
        base = pd.DataFrame(
            columns=["Division", "Reports", "Direct", "New", "Waiting"]
        )
    all_divisions = _division_names()
    base = base.set_index("Division").reindex(all_divisions).reset_index()
    base["Division"] = base["Division"].astype(str)
    for c in NUMERIC_COLS:
        base[c] = pd.to_numeric(base[c], errors="coerce").fillna(0.0)
    return _enrich(base, "Division")


def _district_table(df: pd.DataFrame) -> pd.DataFrame:
    """By district: always all 30 districts, sorted alphabetically."""
    base = breakdown(df, "district")
    if len(base):
        base = base.rename(
            columns={
                "group": "District",
                "reports": "Reports",
                "direct": "Direct",
                "new": "New",
                "waiting": "Waiting",
            }
        )
    else:
        base = pd.DataFrame(
            columns=["District", "Reports", "Direct", "New", "Waiting"]
        )
    code_to_name, all_districts = _district_names()
    base["District"] = base["District"].map(code_to_name).fillna(base["District"])
    base = base.set_index("District").reindex(all_districts).reset_index()
    base["District"] = base["District"].astype(str)
    for c in NUMERIC_COLS:
        base[c] = pd.to_numeric(base[c], errors="coerce").fillna(0.0)
    return _enrich(base, "District")


def render(df: pd.DataFrame, basis: str = "active"):
    """Render the Breakdowns page."""
    st.title("Breakdowns")

    # CHANGED: warn when cumulative is missing implausible rows.
    if basis == "cumulative":
        _warn_invalid_cumulative(df)

    grand_total = aggregate_reach(df, family_factor=FAMILY_FACTOR)["direct"]

    # --- By service ---
    st.markdown("### By service (as filed)")
    svc = _with_grand_total(_service_table(df), "Service")
    st.dataframe(svc, use_container_width=True, hide_index=True)
    table_with_downloads(svc, "Breakdown by service", "bd_service")

    # --- By region (division) ---
    st.markdown("### By region (division)")
    reg = _with_grand_total(_region_table(df), "Division")
    st.dataframe(reg, use_container_width=True, hide_index=True)
    table_with_downloads(reg, "Breakdown by region", "bd_region")

    # --- By district ---
    st.markdown("### By district")
    dist = _with_grand_total(_district_table(df), "District")
    st.dataframe(dist, use_container_width=True, hide_index=True)
    table_with_downloads(dist, "Breakdown by district", "bd_district")

    st.caption(
        f"Grand total (Direct): {grand_total:,.0f} — service, region and district "
        "tables all reconcile to aggregate_reach()."
    )