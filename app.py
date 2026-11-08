import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

"""DEPD Executive Analytics dashboard — local entry point."""
import streamlit as st

from src.ui.components import kpi_card, table_with_downloads
from src.ui.state import get_filtered_dataframe, load_data
from src.kpi.aggregate import aggregate_reach, breakdown

st.set_page_config(page_title="DEPD Dashboard", layout="wide")

st.title("DEPD Executive Analytics")
st.caption("SYNTHETIC TEST DATA — demonstrating the pipeline, not real figures")

# Sidebar navigation (stub — only the Executive page is implemented for now)
page = st.sidebar.radio("Page", ["Executive Overview", "Breakdowns"])

# Role stub (Phase 6 will replace with real auth)
role = st.sidebar.selectbox("Role", ["viewer", "admin"])

# Filter bar
all_df = load_data()
divisions = ["All"] + sorted(all_df["division"].dropna().unique().tolist())
districts = ["All"] + sorted(all_df["district"].dropna().unique().tolist())
services = ["All"] + sorted(all_df["facility_type"].dropna().unique().tolist())

c1, c2, c3, c4 = st.columns(4)
division = c1.selectbox("Division", divisions)
district = c2.selectbox("District", districts)
service = c3.selectbox("Service type", services)
basis = c4.radio("Basis", ["active", "cumulative"], horizontal=True)

filters = {}
if division != "All":
    filters["division"] = division
if district != "All":
    filters["district"] = district
if service != "All":
    filters["service_type"] = service

df = get_filtered_dataframe(basis=basis, **filters)

# Show active filter chips
chip_text = " · ".join(f"{k}={v}" for k, v in filters.items()) or "All Sindh"
st.caption(f"Filters: {chip_text} · Basis: {basis}")

# Page: Executive Overview
if page == "Executive Overview":
    r = aggregate_reach(df)
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        kpi_card(
            "Direct beneficiaries",
            f"{r['direct']:,.0f}",
            "Facility-reported unique headcounts; not deduplicated across facilities",
        )
    with col2:
        kpi_card(
            "Estimated family (×5)",
            f"{r['family']:,.0f}",
            "Estimated, Direct × 5. Model, not a count.",
        )
    with col3:
        kpi_card(
            "Estimated total reach",
            f"{r['total']:,.0f}",
            "Estimated total reach = Direct + family estimate",
        )
    with col4:
        kpi_card("Reports", len(df))
    with col5:
        kpi_card("Facilities", df["facility_name"].nunique())

    st.subheader("Source mix")
    st.write(r["source_mix"])

    st.subheader("Latest 10 reports (institution names only)")
    latest = (
        df.sort_values("_submission_time", ascending=False)
        [["facility_name", "facility_type", "district", "rp_end", "direct", "source", "flags"]]
        .head(10)
    )
    table_with_downloads(latest, "Latest 10 reports", "latest_10")

# Page: Breakdowns
elif page == "Breakdowns":
    st.subheader("By service type (as filed)")
    table_with_downloads(breakdown(df, "service"), "Breakdown by service", "by_service")
    st.subheader("By division (from district mapping)")
    table_with_downloads(breakdown(df, "division"), "Breakdown by division", "by_division")
    st.subheader("By district")
    table_with_downloads(breakdown(df, "district"), "Breakdown by district", "by_district")
