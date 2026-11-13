"""Executive Overview page — headline reach and service cards.

Three tiers:
  Row 1 — Current operations (Direct / Indirect reported / Waiting / Total reach)
  Row 2 — Lifetime totals (Lifetime Direct / All reports combined / Submissions)
  Grid — 18 service cards with bucket badges
"""
from __future__ import annotations

import os

import pandas as pd
import streamlit as st

from src.kpi.aggregate import (
    LIFETIME_TOTALS,
    REGISTRATION_BODIES,
    aggregate_reach,
    aggregate_totals,
)
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
        st.warning("SYNTHETIC TEST DATA — demonstrating the pipeline, not real figures.")

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

    totals = aggregate_totals(view, family_factor=FAMILY_FACTOR)

    # =====================================================================
    # ROW 1 — CURRENT OPERATIONS
    # =====================================================================
    st.markdown("#### Current beneficiaries")
    st.caption(
        "Direct = active/current beneficiaries across 16 service types. "
        "Excludes lifetime totals and registration bodies."
    )
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card(
            "Current Direct",
            f"{totals['current_direct']:,.0f}",
            tooltip="Sum of active beneficiaries across current service types. "
                    "Excludes NOWPDP, Disability Certificates, SPDPA, and Regional Directorate.",
        )
    with c2:
        kpi_card(
            "Indirect (reported)",
            f"{totals['indirect_reported']:,.0f}",
            tooltip="Facility-reported indirect reach (outreach / community). "
                    "This is what the facility itself reported — not the ×F family estimate.",
        )
    with c3:
        kpi_card(
            "Waiting",
            f"{totals['waiting']:,.0f}",
            tooltip="Sum of waiting lists across centres. "
                    "Programme-level waiting for GIA / NOWPDP is de-duplicated.",
        )
    with c4:
        kpi_card(
            "Total reach (current)",
            f"{totals['total_reach_current']:,.0f}",
            tooltip="Current Direct + estimated family reach (Direct × F).",
        )

    # =====================================================================
    # ROW 2 — LIFETIME TOTALS (shown separately, never mixed)
    # =====================================================================
    st.markdown("#### Lifetime totals (since inception)")
    st.caption(
        "These services report cumulative figures since establishment, so they "
        "are shown separately and are NOT comparable to the current headline."
    )
    L1, L2, L3 = st.columns(3)
    with L1:
        kpi_card(
            "Lifetime Direct",
            f"{totals['lifetime_direct']:,.0f}",
            tooltip=(
                f"NOWPDP Programmes {totals['lifetime_nowpdp']:,.0f} + "
                f"Disability Certificates {totals['lifetime_dis_cer']:,.0f}. "
                "Both report since-inception totals."
            ),
        )
    with L2:
        kpi_card(
            "All reports combined",
            f"{totals['combined_direct']:,.0f}",
            tooltip="Current Direct + Lifetime Direct. Matches the Dashboard sheet's "
                    "'Total, all reports' row.",
        )
    with L3:
        kpi_card(
            "Submissions",
            f"{totals['n_reports_current'] + totals['n_reports_lifetime']:,}",
            tooltip="Submissions in the current filter, split across current + lifetime buckets.",
        )

    # =====================================================================
    # SERVICES GRID — 18 cards grouped by category
    # =====================================================================
    st.markdown("### Services")
    st.caption(
        "NOWPDP and Disability Certificates are lifetime totals. "
        "SPDPA and Regional Directorate are registration / administrative bodies — "
        "not service beneficiaries."
    )

    headline_direct = float(totals["current_direct"])
    service_direct_sum = 0.0
    for category, codes in SERVICE_ORDER:
        st.subheader(category)
        cols = st.columns(3)
        for i, code in enumerate(codes):
            subset = view[view["facility_type"].astype(str) == code]
            with cols[i % 3]:
                render_service_card(code, subset, FAMILY_FACTOR)
                # Only count current services toward reconciliation
                if len(subset) and code not in LIFETIME_TOTALS and code not in REGISTRATION_BODIES:
                    service_direct_sum += float(
                        pd.to_numeric(subset.get("direct", 0.0), errors="coerce")
                        .fillna(0.0)
                        .sum()
                    )

    match = abs(service_direct_sum - headline_direct) < 0.1
    st.caption(
        "Reconciliation: sum of current service Direct = "
        f"{service_direct_sum:,.0f}; current headline Direct = "
        f"{headline_direct:,.0f}. Match: {'yes' if match else 'no'}."
    )
    if not match:
        print(
            "EXEC RECONCILIATION MISMATCH: service sum "
            f"{service_direct_sum} vs current headline {headline_direct}"
        )