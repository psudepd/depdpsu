"""Service summaries page.

One pivot per service type: Region → District → Organization Name, with
Beneficiaries, Records, and an auto-generated Note. Each service section
has its own Excel and JPG download via table_with_downloads.

Layout is derived from the Summary sheet in DEPD_Beneficiary_Data_with_Summary.xlsx,
but the Region column comes from division_mapped (not the raw `division`
field) so it matches the Executive and Breakdowns pages.
"""
from __future__ import annotations

import os

import pandas as pd
import streamlit as st

from src.kpi.aggregate import LIFETIME_TOTALS, REGISTRATION_BODIES, aggregate_reach
from src.ui.components import table_with_downloads
from src.ui.service_cards import SERVICE_ORDER, _load_labels

FAMILY_FACTOR = int(os.environ.get("FAMILY_FACTOR", "5"))

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))
DISTRICT_DIVISION_PATH = os.path.join(_REPO_ROOT, "data", "district_division.csv")


def _district_name_map() -> dict:
    """district_code -> display name from district_division.csv."""
    try:
        dd = pd.read_csv(DISTRICT_DIVISION_PATH, dtype=object)
        return {
            str(r["district_code"]).strip(): str(r["district_name"]).strip()
            for _, r in dd.iterrows()
        }
    except Exception:
        return {}


def _summary_table(subset: pd.DataFrame, code: str) -> pd.DataFrame:
    """Region / District / Organization pivot for one service.

    Grouped by (division_mapped, district, facility_name). One row per
    organisation. Beneficiaries = sum of direct. Records = count. Note is
    auto-generated: "0 beneficiaries reported" when Direct == 0 and Records > 0.

    Returns an empty DataFrame if subset is empty.
    """
    cols = ["Region", "District", "Organization Name", "Beneficiaries", "Records", "Note"]
    if subset is None or len(subset) == 0:
        return pd.DataFrame(columns=cols)

    d = subset.copy()

    # Region: prefer division_mapped (display name); fall back to raw division
    if "division_mapped" in d.columns:
        region = d["division_mapped"].astype(str).str.strip()
    else:
        region = d.get("division", pd.Series([""] * len(d), index=d.index)).astype(str).str.strip()
    d["_region"] = region

    # District: display name via code map, fall back to raw value
    dmap = _district_name_map()
    district = d.get("district", pd.Series([""] * len(d), index=d.index)).astype(str).str.strip()
    d["_district"] = district.map(lambda c: dmap.get(c, c))

    # Organization: facility_name, blank rows become "(unnamed)"
    org = d.get("facility_name", pd.Series([""] * len(d), index=d.index)).astype(str).str.strip()
    d["_org"] = org.where(org != "", "(unnamed)")

    # Beneficiaries: sum of direct
    d["_direct"] = pd.to_numeric(d.get("direct", 0.0), errors="coerce").fillna(0.0)

    grouped = (
        d.groupby(["_region", "_district", "_org"], dropna=False)
        .agg(Beneficiaries=("_direct", "sum"), Records=("_direct", "size"))
        .reset_index()
        .rename(columns={"_region": "Region", "_district": "District", "_org": "Organization Name"})
    )

    # Auto-note
    def _note(row):
        if float(row["Beneficiaries"]) == 0 and int(row["Records"]) > 0:
            return "0 beneficiaries reported"
        return ""

    grouped["Note"] = grouped.apply(_note, axis=1)

    # Sort by Region, then District, then Organization
    grouped = grouped.sort_values(
        ["Region", "District", "Organization Name"], kind="stable"
    ).reset_index(drop=True)

    return grouped[cols]


def _with_grand_total(tbl: pd.DataFrame) -> pd.DataFrame:
    """Append a grand total row whose Beneficiaries equals aggregate_reach on the subset."""
    if tbl is None or len(tbl) == 0:
        return tbl
    total_ben = float(tbl["Beneficiaries"].sum())
    total_rec = int(tbl["Records"].sum())
    gt = {
        "Region": "Grand total",
        "District": "",
        "Organization Name": "",
        "Beneficiaries": total_ben,
        "Records": total_rec,
        "Note": "",
    }
    return pd.concat([tbl, pd.DataFrame([gt])], ignore_index=True)


def _service_heading(code: str, labels: dict) -> str:
    """Human heading for a service section."""
    label = labels.get(code, code)
    return f"{code} — {label}"


def render(df: pd.DataFrame, basis: str = "active"):
    """Render the Service summaries page."""
    st.title("Service summaries")
    st.caption(
        "One pivot per service type. Rows group by Region → District → "
        "Organization Name (from the facility_name field). Beneficiaries = sum "
        "of Direct for that organisation. Each section has its own Excel and "
        "JPG download."
    )

    if df is None or len(df) == 0:
        st.warning("No submissions match the current filters.")
        return

    labels = _load_labels()

    for category, codes in SERVICE_ORDER:
        st.header(category)
        for code in codes:
            subset = df[df["facility_type"].astype(str) == code]
            heading = _service_heading(code, labels)

            # Bucket badge in the section header for lifetime/registration services
            if code in LIFETIME_TOTALS:
                st.subheader(f"{heading}  ·  :orange[Lifetime total]")
            elif code in REGISTRATION_BODIES:
                st.subheader(f"{heading}  ·  :grey[Registration / admin body]")
            else:
                st.subheader(heading)

            if len(subset) == 0:
                st.caption("No reports for this service in the current filter.")
                st.markdown("---")
                continue

            table = _summary_table(subset, code)
            table_with_total = _with_grand_total(table)

            # Reconcile: grand total Beneficiaries should equal aggregate_reach on subset
            headline = float(aggregate_reach(subset, family_factor=FAMILY_FACTOR)["direct"])
            table_total = float(table["Beneficiaries"].sum())
            match = abs(table_total - headline) < 0.1
            if not match:
                st.caption(
                    f":red[Reconciliation mismatch for {code}: table sum "
                    f"{table_total:,.0f} vs aggregate_reach {headline:,.0f}.]"
                )

            table_with_downloads(
                table_with_total,
                f"sum_{code} — {labels.get(code, code)}",
                f"sum_{code}",
            )
            st.markdown("---")

    st.caption(
        "Grand total row per section reconciles to aggregate_reach() for that "
        "service. Note is auto-generated: '0 beneficiaries reported' when "
        "Beneficiaries = 0 and Records > 0; blank otherwise."
    )