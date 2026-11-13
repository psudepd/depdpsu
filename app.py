"""DEPD Executive Analytics dashboard — local entry point."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import streamlit as st

from src.ui.state import DATA_SOURCE, get_filtered_dataframe, load_data
from src.kpi.aggregate import aggregate_totals
from src.kpi.geography import add_division_columns
from src.ui.pages.executive import render as render_executive
from src.ui.pages.breakdowns import render as render_breakdowns
from src.ui.pages.map import render as render_map

FAMILY_FACTOR = int(os.environ.get("FAMILY_FACTOR", "5"))

st.set_page_config(page_title="DEPD Dashboard", layout="wide")

st.title("DEPD Executive Analytics")
if DATA_SOURCE == "live":
    st.caption("Data source: LIVE (KoboToolbox)")
else:
    st.caption("Data source: SYNTHETIC · demonstrating the pipeline, not real figures")

# Sidebar navigation (stub — only the Executive page is implemented for now)
page = st.sidebar.radio("Page", ["Executive Overview", "Breakdowns", "Map"])

# Role stub (Phase 6 will replace with real auth)
role = st.sidebar.selectbox("Role", ["viewer", "admin"])


# --- Load raw data (cached once) and enrich with mapped division names ----
@st.cache_data(ttl=300, show_spinner="Loading filter options…")
def _load_all():
    return load_data()


all_df = _load_all()
try:
    all_df_enriched = add_division_columns(all_df)
except Exception:
    all_df_enriched = all_df


# --- District code -> display name mapping (for the dropdown) ------------
_DD_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "data", "district_division.csv"
)
try:
    _dd = pd.read_csv(_DD_PATH, dtype=object)
    _district_code_to_name = {
        str(r["district_code"]).strip(): str(r["district_name"]).strip()
        for _, r in _dd.iterrows()
    }
except Exception:
    _district_code_to_name = {}


# --- Build dropdown option lists -----------------------------------------
# Division: prefer the mapped display name so it matches get_filtered_dataframe
if "division_mapped" in all_df_enriched.columns:
    _division_values = (
        all_df_enriched["division_mapped"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )
else:
    _division_values = (
        all_df_enriched.get("division", pd.Series(dtype=str))
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )
divisions = ["All"] + sorted(_division_values)

# District: show display name, filter on code
_district_codes = (
    all_df_enriched.get("district", pd.Series(dtype=str))
    .dropna()
    .astype(str)
    .str.strip()
    .unique()
    .tolist()
)
_district_pairs = sorted(
    ((_district_code_to_name.get(c, c), c) for c in _district_codes),
    key=lambda p: p[0],
)
district_labels = ["All"] + [label for label, _ in _district_pairs]
_label_to_code = {label: code for label, code in _district_pairs}
_label_to_code["All"] = "All"

# Service
services = ["All"] + sorted(
    all_df_enriched.get("facility_type", pd.Series(dtype=str))
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)


# --- Filter bar ----------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)
division = c1.selectbox("Division", divisions)
district_label = c2.selectbox("District", district_labels)
service = c3.selectbox("Service type", services)
basis = c4.radio("Basis", ["active", "cumulative"], horizontal=True)

filters = {}
if division != "All":
    filters["division"] = division
if district_label != "All":
    filters["district"] = _label_to_code[district_label]
if service != "All":
    filters["service_type"] = service

df = get_filtered_dataframe(basis=basis, **filters)

# Show active filter chips
chip_text = " · ".join(f"{k}={v}" for k, v in filters.items()) or "All Sindh"
st.caption(f"Filters: {chip_text} · Basis: {basis}")


# --- Home strip: headline answers before clicking a page -----------------
_totals = aggregate_totals(df, family_factor=FAMILY_FACTOR)
st.markdown("---")
h1, h2, h3, h4 = st.columns(4)
h1.metric("Current beneficiaries", f"{_totals['current_direct']:,.0f}")
h2.metric("Lifetime totals", f"{_totals['lifetime_direct']:,.0f}")
h3.metric("Waiting", f"{_totals['waiting']:,.0f}")
h4.metric("All reports combined", f"{_totals['combined_direct']:,.0f}")
st.caption(
    f"Split — Current {_totals['current_direct']:,.0f} · "
    f"Lifetime {_totals['lifetime_direct']:,.0f} "
    f"(NOWPDP {_totals['lifetime_nowpdp']:,.0f} + "
    f"Dis. Cert. {_totals['lifetime_dis_cer']:,.0f})"
)
st.markdown("---")


# --- Page routing --------------------------------------------------------
if page == "Executive Overview":
    render_executive(df, basis)
elif page == "Breakdowns":
    render_breakdowns(df, basis)
elif page == "Map":
    render_map(df, basis)