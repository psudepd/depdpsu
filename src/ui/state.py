"""UI state: load and filter the submissions dataframe.

DATA_SOURCE is env-driven:
  - reads DATA_SOURCE (or DEPD_DATA_SOURCE) from env
  - defaults to "live" if KOBO_EXPORT_URL is set, otherwise "synthetic"
  - if "live", calls src.ingest.kobo_live.load_live() and uses the returned general_df
  - if "synthetic", reads data/synthetic_submissions.csv
"""
from __future__ import annotations

import os

from dotenv import load_dotenv
load_dotenv()

import pandas as pd

from src.kpi.aggregate import select_latest_per_facility
from src.kpi.geography import add_division_columns
from src.kpi.resolver import resolve_dataframe


def _detect_data_source() -> str:
    explicit = os.environ.get("DATA_SOURCE") or os.environ.get("DEPD_DATA_SOURCE")
    if not explicit:
        try:
            import streamlit as st
            explicit = st.secrets.get("DATA_SOURCE") or st.secrets.get("DEPD_DATA_SOURCE")
        except Exception:
            pass
    if explicit:
        return explicit.strip().lower()

    url = os.environ.get("KOBO_EXPORT_URL")
    if not url:
        try:
            import streamlit as st
            url = st.secrets.get("KOBO_EXPORT_URL")
        except Exception:
            pass
    if url:
        return "live"

    return "synthetic"


DATA_SOURCE = _detect_data_source()


def load_data() -> pd.DataFrame:
    """Load submissions for now.

    DATA_SOURCE=synthetic (default) reads data/synthetic_submissions.csv.
    DATA_SOURCE=live reads from kobo_live.load_live() and uses general_df.
    """
    global DATA_SOURCE
    DATA_SOURCE = _detect_data_source()
    if DATA_SOURCE == "live":
        from src.ingest.kobo_live import load_live

        general_df, _restricted_df = load_live()
        return general_df
    return pd.read_csv("data/synthetic_submissions.csv", dtype=object)


def get_filtered_dataframe(
    division=None,
    district=None,
    service_type=None,
    period=None,
    basis="active",
) -> pd.DataFrame:
    """Return the single filtered dataframe used by every page."""
    df = load_data()
    df = select_latest_per_facility(df)
    df = add_division_columns(df)
    df = resolve_dataframe(df, basis=basis)
    if division is not None:
        df = df[df["division_mapped"] == division]
    if district is not None:
        df = df[df["district"] == district]
    if service_type is not None:
        df = df[df["facility_type"] == service_type]
    if period is not None:
        df = df[df["rp_end"] == period]
    return df.reset_index(drop=True)
