"""Executive Overview page — headline reach and service cards.

Page layout (in order):
  1. Page title: "Executive Overview"
  2. Data-source caption ("Data source: LIVE" or "SYNTHETIC")
  3. Three headline KPI cards in a single row (Direct / Indirect (Estimated) /
     Total reach) — short labels, long explanation in the tooltip
  4. "Services (18)" section: one card per service, grouped by category,
     each inside st.container(border=True)
  5. Reconciliation caption: sum of service Direct vs headline Direct

regional_dir is office information only — no card, not counted in totals.
Clicking a card stores the service in st.session_state["executive_service_filter"]
and re-computes the headline row on that subset.
"""
from __future__ import annotations

import os

import pandas as pd
import streamlit as st

from src.kpi.aggregate import aggregate_reach
from src.ui.components import kpi_card
from src.ui.service_cards import SERVICE_ORDER, render_service_card
from src.ui.state import DATA_SOURCE

FAMILY_FACTOR = int(os.environ.get("FAMILY_FACTOR", "5"))


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


def render(df: pd.DataFrame, basis: str = "active"):
    """Render the Executive Overview page."""
    st.title("Executive Overview")
    source_label = "LIVE" if DATA_SOURCE == "live" else "SYNTHETIC"
    st.caption(f"Data source: {source_label}")
    if DATA_SOURCE != "live":
        st.warning(
            "SYNTHETIC TEST DATA — demonstrating the pipeline, not real figures."
        )

    # CHANGED: warn when cumulative is missing implausible rows.
    if basis == "cumulative":
        _warn_invalid_cumulative(df)

    # --- Service filter state (this page only) ---
    service_filter = st.session_state.get("executive_service_filter")
    view = df
    if service_filter:
        view = df[df["facility_type"].astype(str) == service_filter]
        if st.button("Reset service filter", key="exec_reset_filter"):
            st.session_state["executive_service_filter"] = None
            st.rerun()

    # --- Headline reach cards (re-computes on the service subset when set) ---
    r = aggregate_reach(view, family_factor=FAMILY_FACTOR)
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

    # --- Services (18): one card per service, grouped by category ---
    st.markdown("### Services (18)")
    headline_direct = float(r["direct"])
    service_direct_sum = 0.0
    for category, codes in SERVICE_ORDER:
        st.subheader(category)
        cols = st.columns(3)
        for i, code in enumerate(codes):
            subset = view[view["facility_type"].astype(str) == code]
            with cols[i % 3]:
                render_service_card(code, subset, FAMILY_FACTOR)
                if len(subset):
                    service_direct_sum += float(
                        pd.to_numeric(subset.get("direct", 0.0), errors="coerce")
                        .fillna(0.0)
                        .sum()
                    )

    match = abs(service_direct_sum - headline_direct) < 0.1
    st.caption(
        "Reconciliation: sum of service Direct = "
        f"{service_direct_sum:,.0f}; headline Direct = {headline_direct:,.0f}. "
        f"Match: {'yes' if match else 'no'}."
    )
    if not match:
        print(
            "EXEC RECONCILIATION MISMATCH: service sum "
            f"{service_direct_sum} vs headline {headline_direct}"
        )