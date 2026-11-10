"""GIS map page.

Map + four panels:
  (1) Headline: Direct, Estimated family, Estimated total
  (2) Direct by service type: 18 cards
  (3) Data received: reports, facilities, districts x/30, last submission,
      source mix, latest 10 reports
  (4) Filters above the map: service type, ownership class, region, district

Boundary policy (interim): district polygon layers are deferred until a
licensed ADM2 file is available. Pins render on OpenStreetMap only.
No polygon geometry, no bbox filtering, no district containment checks.
"""
from __future__ import annotations

import os

import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from src.export.exporters import footer_text
from src.geo.boundaries import load_boundaries
from src.geo.render_folium import build_folium_map, missing_boundaries_html
from src.geo.render_static import render_static_jpg
from src.kpi.aggregate import aggregate_reach, breakdown
from src.kpi.geography import DIVISION_MAP
from src.ui.components import kpi_card, table_with_downloads
from src.ui.state import DATA_SOURCE, get_filtered_dataframe, load_data

FAMILY_FACTOR = int(os.environ.get("FAMILY_FACTOR", "5"))
DISTRICTS_TOTAL = 30

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


def _render_map_or_fallback(df: pd.DataFrame):
    # Boundary layers deferred. Pins on OpenStreetMap, no polygons.
    st.info(
        "Interactive map: facility pins on OpenStreetMap. "
        "District-level boundary shading is not enabled yet."
    )
    fmap = build_folium_map(df, None)   # None forces the pin-only path
    if fmap is None:
        st.info("Map unavailable.")
        return
    st_folium(fmap, use_container_width=True, height=700, key="depd_map")

    missing = getattr(fmap, "_missing_rows", None)
    if missing is not None and len(missing):
        with st.expander("Submissions without coordinates", expanded=False):
            st.dataframe(
                missing.rename(columns={
                    "facility_name": "Facility",
                    "district": "District",
                    "reason": "Reason",
                }),
                use_container_width=True,
                hide_index=True,
            )


def _headline_panel(df: pd.DataFrame):
    r = aggregate_reach(df, family_factor=FAMILY_FACTOR)
    kpi_card("Direct beneficiaries", f"{r['direct']:,.0f}",
             "Facility-reported unique headcounts (resolved per Section 5.3).")
    kpi_card("Estimated family (indirect)", f"{r['family']:,.0f}",
             f"Estimated model: Direct × {FAMILY_FACTOR}. Not a count.")
    kpi_card("Estimated total reach", f"{r['total']:,.0f}",
             "Estimated total reach = Direct + family estimate.")


def _service_cards(df: pd.DataFrame):
    st.markdown("**Direct by service type (18)**")
    bt = breakdown(df, "service")
    types = [
        "rcmhc", "rcph", "gov_se", "inclusive", "deaf_reach", "sipmr", "ipmr",
        "carts", "nowpdp", "hostel", "vtc", "academy", "gia",
        "sindh_persons_with_disabilitie", "dis_cer",
        "legal_support__beneficiaries", "pcrdp", "assistive_ip",
    ]
    by_type = {}
    if len(bt):
        by_type = dict(zip(bt["group"].astype(str), bt["direct"]))
    cols = st.columns(3)
    for i, t in enumerate(types):
        with cols[i % 3]:
            val = by_type.get(t, 0.0)
            status = "No reports" if val == 0 and t not in by_type else ""
            kpi_card(t, f"{val:,.0f}" + ("" if status == "" else " · No reports"))


def _data_received_panel(df: pd.DataFrame):
    st.markdown("**Data received**")
    r = aggregate_reach(df, family_factor=FAMILY_FACTOR)
    kpi_card("Reports received", len(df))
    kpi_card("Distinct facilities", df["facility_name"].nunique() if len(df) else 0)
    d_rep = (
        df[df["district"].notna() & (df["district"].astype(str).str.strip() != "")]
        if len(df)
        else df
    )
    kpi_card("Districts reporting", f"{d_rep['district'].nunique()}/{DISTRICTS_TOTAL}")
    st.caption("Last submission time (Asia/Karachi)")
    if len(df) and "_submission_time" in df.columns:
        times = pd.to_datetime(df["_submission_time"], errors="coerce").dropna()
        ts = times.max().strftime("%Y-%m-%d %H:%M") if len(times) else "—"
        st.caption(ts)
    else:
        st.caption("—")
    st.markdown("**Source mix**")
    st.write(r.get("source_mix", {}) or "No data")
    st.markdown("**Latest 10 reports**")
    if len(df):
        wanted = ["facility_name", "facility_type", "district", "rp_end",
                  "_submission_time", "direct"]
        present = [c for c in wanted if c in df.columns]
        if "_submission_time" in df.columns:
            latest = (
                df.sort_values("_submission_time", ascending=False)
                  [present]
                  .head(10)
            )
        else:
            latest = df[present].head(10)
        table_with_downloads(latest, "Latest 10 reports", "map_latest_10")
    else:
        st.info("No reports in selection")


def render(df: pd.DataFrame, basis: str = "active"):
    """Render the GIS map page."""
    st.title("DEPD Geographic Coverage")
    if DATA_SOURCE != "live":
        st.warning(
            "SYNTHETIC TEST DATA — demonstrating the pipeline, not real figures."
        )

    st.caption(f"Basis: {basis}")

    ownership_by_type = _ownership_by_type()
    all_df = load_data()

    # --- Filter options (deduplicated) ---
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

    map_col, panel_col = st.columns([4, 2])
    with map_col:
        st.markdown("**Sindh facilities on OpenStreetMap**")
        _render_map_or_fallback(fdf)
    with panel_col:
        st.markdown("### Headline")
        _headline_panel(fdf)
        st.markdown("---")
        st.markdown("### Direct by service type")
        _service_cards(fdf)
        st.markdown("---")
        st.markdown("### Data received")
        _data_received_panel(fdf)