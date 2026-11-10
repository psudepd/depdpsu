"""Service cards for the Executive Overview page.

Pure presentation helper: loads the human service labels from
data/choices.csv (list_name == "facility_types") and the ownership
class colour from data/ownership_by_type.csv, then renders one card per
service inside st.container(border=True).

regional_dir is office information only and is deliberately excluded
from SERVICE_ORDER (18 service types).
"""
from __future__ import annotations

import os

import pandas as pd
import streamlit as st

# CHANGED: _HERE is .../src/ui; two dirnames (not three) reach the repo root.
_HERE = os.path.dirname(os.path.abspath(__file__))          # .../src/ui
_SRC = os.path.dirname(_HERE)                               # .../src
_REPO_ROOT = os.path.dirname(_SRC)                          # .../DEPD Dashboard Beneficiary
CHOICES_PATH = os.path.join(_REPO_ROOT, "data", "choices.csv")
OWNERSHIP_PATH = os.path.join(_REPO_ROOT, "data", "ownership_by_type.csv")

OWNERSHIP_COLOUR = {
    "government": "#2E7D32",
    "partner": "#1F5FBF",
    "other": "#7B3FA0",
    "unknown": "#6B7280",
}

# (category label, [facility_type codes]) — 18 services; regional_dir excluded.
SERVICE_ORDER: list[tuple[str, list[str]]] = [
    ("Education", ["gov_se", "inclusive", "deaf_reach", "academy"]),
    ("Health / rehabilitation", ["rcmhc", "rcph", "sipmr", "ipmr"]),
    ("Training / vocational", ["carts", "vtc", "nowpdp"]),
    ("Hostel / residential", ["hostel"]),
    ("Assistive devices", ["assistive_ip"]),
    (
        "Registration / legal",
        [
            "sindh_persons_with_disabilitie",
            "dis_cer",
            "legal_support__beneficiaries",
            "pcrdp",
        ],
    ),
    ("Grant-in-aid", ["gia"]),
]


# CHANGED: cache the two static CSV loads; they never change at runtime.
@st.cache_data(show_spinner=False)
def _load_labels() -> dict:
    """facility_type code -> human label from choices.csv."""
    df = pd.read_csv(CHOICES_PATH, dtype=object)
    sub = df[df["list_name"] == "facility_types"]
    return {str(k).strip(): str(v).strip() for k, v in zip(sub["name"], sub["label"])}


@st.cache_data(show_spinner=False)
def _load_ownership() -> dict:
    """facility_type code -> ownership class."""
    df = pd.read_csv(OWNERSHIP_PATH, dtype=object)
    return {
        str(k).strip(): str(v).strip()
        for k, v in zip(df["facility_type"], df["ownership_class"])
    }


def _colour_for(code: str, ownership: dict) -> str:
    return OWNERSHIP_COLOUR.get(
        ownership.get(code, "unknown"), OWNERSHIP_COLOUR["unknown"]
    )


def _gender_w_only(subset: pd.DataFrame):
    """Male / Female / Other from rows where source == "W".

    Returns (male, female, other, has_any).
    """
    if subset.empty or "source" not in subset.columns:
        return 0.0, 0.0, 0.0, False
    w = subset[subset["source"].astype(str) == "W"]
    if w.empty:
        return 0.0, 0.0, 0.0, False
    male = float(
        pd.to_numeric(w.get("w_male", 0.0), errors="coerce").fillna(0.0).sum()
    )
    female = float(
        pd.to_numeric(w.get("w_female", 0.0), errors="coerce").fillna(0.0).sum()
    )
    other = float(
        pd.to_numeric(w.get("w_other", 0.0), errors="coerce").fillna(0.0).sum()
    )
    return male, female, other, bool((male + female + other) > 0)


def render_service_card(code: str, subset: pd.DataFrame, factor: int) -> float:
    """Render one service card; returns its Direct value (0.0 if no reports).

    Card layout inside st.container(border=True):
      a. coloured dot + human label (ownership colour from ownership_by_type.csv)
      b. human label from choices.csv
      c. Direct and Indirect (Estimated) side by side
      d. Male / Female / Other from W-only rows, or "Gender not reported"
      e. number of reports
      f. grey "Data not received" card (numerics hidden) when zero reports
    """
    labels = _load_labels()
    ownership = _load_ownership()
    colour = _colour_for(code, ownership)
    human_label = labels.get(code, code)

    has_reports = len(subset) > 0
    if has_reports:
        direct = float(
            pd.to_numeric(
                subset.get("direct", pd.Series([0.0] * len(subset))),
                errors="coerce",
            )
            .fillna(0.0)
            .sum()
        )
    else:
        direct = 0.0
    indirect = direct * factor
    n_reports = int(len(subset))

    with st.container(border=True):
        st.markdown(
            "<span style='display:inline-block;width:9px;height:9px;"
            f"border-radius:50%;background:{colour};margin-right:6px;'></span>"
            f"<b>{human_label}</b>",
            unsafe_allow_html=True,
        )
        if not has_reports:
            st.markdown(":grey[**Data not received**]")
            return 0.0

        c1, c2 = st.columns(2)
        c1.metric("Direct", f"{direct:,.0f}")
        c2.metric("Indirect (Estimated)", f"{indirect:,.0f}")

        male, female, other, has_any = _gender_w_only(subset)
        if has_any:
            st.caption(
                f"Male {male:,.0f} · Female {female:,.0f} · Other {other:,.0f}"
            )
        else:
            st.caption("Gender not reported")

        st.caption(f"Reports: {n_reports}")

        if st.button(
            "Select service", key=f"exec_svc_{code}", use_container_width=True
        ):
            st.session_state["executive_service_filter"] = code
            st.rerun()

    return direct