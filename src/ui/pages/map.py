"""GIS map page — map, filters and headline reach only.

Page layout (in order):
  1. Page title: "Geographic Coverage"
  2. Filter bar: Service type, Ownership class, Region, District
  3. Three headline KPI cards: Direct, Indirect (Estimated), Total reach
  4. Folium map, full width, height=700
  5. Optional collapsible "Submissions without coordinates" expander

The 18-service cards grid, the "Data received" panel, the "Latest 10
reports" table and any source-mix text are removed from this page.
build_folium_map() and render_folium.py are not touched.
"""
from __future__ import annotations

import os

import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from src.geo.render_folium import build_folium_map
from src.kpi.aggregate import aggregate_reach
from src.kpi.geography import DIVISION_MAP
from src.ui.components import kpi_card
from src.ui.state import DATA_SOURCE, load_data

FAMILY_FACTOR = int(os.environ.get("FAMILY_FACTOR", "5"))

# map.py is at repo/src/ui/pages/map.py — 4 dirname calls to reach repo root.
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(_HERE))
)
OWNERSHIP_PATH = os.path.join(_REPO_ROOT, "data", "ownership_by_type.csv")

_OWNERSHIP_FALLBACK = {
    "rcmhc": "government",
    "rcph": "government",
    "gov_se": "government",
    "inclusive": "government",
    "deaf_reach": "partner",
    "sipmr": "other",
    "ipmr": "other",
    "carts": "government",
    "nowpdp": "other",
    "hostel": "other",
    "vtc": "government",
    "academy": "other",
    "gia": "partner",
    "sindh_persons_with_disabilitie": "government",
    "dis_cer": "government",
    "legal_support__beneficiaries": "other",
    "pcrdp": "other",
    "assistive_ip": "partner",
    "regional_dir": "government",
}


def _ownership_by_type() -> dict:
    try:
        df = pd.read_csv(OWNERSHIP_PATH)
        return {
            str(r["facility_type"]).strip(): str(r["ownership_class"]).strip()
            for _, r in df.iterrows()
        }
    except FileNotFoundError:
        st.warning(
            f"ownership_by_type.csv not found at {OWNERSHIP_PATH}. "
            "Using built-in fallback ownership classes."
        )
        return dict(_OWNERSHIP_FALLBACK)


def _render_map(df: pd.DataFrame):
    """Render the Folium map full-width with the missing-coordinates expander."""
    st.info(
        "Interactive map: facility pins on OpenStreetMap. "
        "District-level boundary shading is not enabled yet."
    )
    fmap = build_folium_map(df, None)  # None forces the pin-only path
    if fmap is None:
        st.info("Map unavailable.")
        return

    st_folium(fmap, use_container_width=True, height=700, key="depd_map")

    missing = getattr(fmap, "_missing_rows", None)
    if missing is not None and len(missing):
        with st.expander("Submissions without coordinates", expanded=False):
            st.dataframe(
                missing.rename(
                    columns={
                        "facility_name": "Facility",
                        "district": "District",
                        "reason": "Reason",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )


def render(df: pd.DataFrame, basis: str = "active"):
    """Render the GIS map page: title, filters, headline reach, map."""
    st.title("Geographic Coverage")
    source_label = "LIVE" if DATA_SOURCE == "live" else "SYNTHETIC"
    st.caption(f"Data source: {source_label}")
    if DATA_SOURCE != "live":
        st.warning(
            "SYNTHETIC TEST DATA — demonstrating the pipeline, not real figures."
        )

    # --- Filter bar (4 columns, deduped lists) ---
    ownership_by_type = _ownership_by_type()
    all_df = load_data()

    services = ["All"] + sorted(all_df["facility_type"].dropna().unique().tolist())
    ownership_classes = ["All"] + sorted(set(ownership_by_type.values()))
    regions = ["All"] + sorted(set(DIVISION_MAP.values()))     # 6 divisions
    districts = ["All"] + sorted(set(DIVISION_MAP.keys()))     # 30 districts

    f1, f2, f3, f4 = st.columns(4)
    svc = f1.selectbox("Service type", services, key="map_service")
    own = f2.selectbox("Ownership class", ownership_classes, key="map_ownership")
    reg = f3.selectbox("Region (division)", regions, key="map_region")
    dist = f4.selectbox("District", districts, key="map_district")

    fdf = df.copy()
    if svc != "All":
        fdf = fdf[fdf["facility_type"].astype(str) == svc]
    if own != "All":
        allowed = {t for t, c in ownership_by_type.items() if c == own}
        fdf = fdf[fdf["facility_type"].astype(str).isin(allowed)]
    if reg != "All":
        fdf = fdf[fdf["division_mapped"].astype(str) == reg]
    if dist != "All":
        fdf = fdf[fdf["district"].astype(str) == dist]

    chip = " · ".join(
        f"{k}={v}" for k, v in {
            "service": svc, "ownership": own, "region": reg, "district": dist,
        }.items() if v != "All"
    ) or "All Sindh"
    st.caption(f"Filters: {chip} · Basis: {basis}")

    # --- Headline reach cards (single row, short labels, tooltips) ---
    r = aggregate_reach(fdf, family_factor=FAMILY_FACTOR)
    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card(
            "Direct",
            f"{r['direct']:,.0f}",
            tooltip="Facility-reported unique headcounts. Resolved per Section 5.3; not deduplicated across facilities.",
        )
    with c2:
        kpi_card(
            "Indirect (Estimated)",
            f"{r['family']:,.0f}",
            tooltip="Estimated model: Direct × F (F=5 by default). Not a count.",
        )
    with c3:
        kpi_card(
            "Total reach",
            f"{r['total']:,.0f}",
            tooltip="Estimated total reach = Direct + indirect (Direct × (1+F)).",
        )

    # --- Map (full width) ---
    _render_map(fdf)