"""KPI aggregation helpers built on top of src/kpi/resolver.py.

Reads canonical (already-resolved or resolvable) submission frames and
produces headline reach figures, breakdowns and sanity flags.  Never
re-resolves rows that already carry a numeric ``direct`` column.
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

import pandas as pd

from src.kpi.resolver import (
    CUM_FIELDS,
    FAMILY_FACTOR,
    num,
    resolve_active,
)

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(HERE, os.pardir, os.pardir))
DISTRICT_DIVISION_PATH = os.path.join(PROJECT_ROOT, "data", "district_division.csv")
DIVISIONS_PATH = os.path.join(PROJECT_ROOT, "data", "divisions.csv")

NEW_FIELDS = ("w_new", "c_new", "n_new")
WAITING_FIELDS = ("w_waiting", "c_waiting", "n_waiting")

SANITY_CEILING = 1_000_000

# --- NEW: tier classification for the Executive page -------------------------
# Lifetime-since-inception totals — never mixed into the "current" headline.
LIFETIME_TOTALS = frozenset({"nowpdp", "dis_cer"})
# Registration / administrative bodies — not beneficiary counts.
REGISTRATION_BODIES = frozenset({"sindh_persons_with_disabilitie", "regional_dir"})

# Fallback division mapping. Mirrors data/district_division.csv + divisions.csv
# exactly. Used ONLY if the CSVs cannot be read at runtime (e.g., the deployed
# bundle does not include data/). Prevents the app from silently returning
# "unknown" for every division.
_DIVISION_NAME_FALLBACK = {
    "karachi": "Karachi",
    "hyderabad": "Hyderabad",
    "shaheed_benazirabad": "Shaheed Benazirabad",
    "mirpurkhas": "Mirpurkhas",
    "sukkur": "Sukkur",
    "larkana": "Larkana",
}

_DISTRICT_CODE_TO_DIVISION_CODE_FALLBACK = {
    "karachi_central": "karachi",
    "karachi_east": "karachi",
    "karachi_south": "karachi",
    "karachi_west": "karachi",
    "korangi": "karachi",
    "malir": "karachi",
    "keamari": "karachi",
    "hyderabad": "hyderabad",
    "badin": "hyderabad",
    "dadu": "hyderabad",
    "jamshoro": "hyderabad",
    "matiari": "hyderabad",
    "tando_allahyar": "hyderabad",
    "tando_muhammad_khan": "hyderabad",
    "thatta": "hyderabad",
    "sujawal": "hyderabad",
    "shaheed_benazirabad": "shaheed_benazirabad",
    "sanghar": "shaheed_benazirabad",
    "naushahro_feroze": "shaheed_benazirabad",
    "mirpurkhas": "mirpurkhas",
    "umerkot": "mirpurkhas",
    "tharparkar": "mirpurkhas",
    "sukkur": "sukkur",
    "khairpur": "sukkur",
    "ghotki": "sukkur",
    "larkana": "larkana",
    "kamber_shahdadkot": "larkana",
    "jacobabad": "larkana",
    "kashmore": "larkana",
    "shikarpur": "larkana",
}


def _norm_name(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    return str(v).strip().lower()


def _norm_district(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    return str(v).strip().lower().replace(" ", "_")


def _first_non_blank(row, cols, ceiling: Optional[float] = None) -> float:
    """First non-blank numeric value; optionally reject anything > ceiling."""
    for c in cols:
        if c in row.index:
            v = num(row[c])
            if v is not None and (ceiling is None or v <= ceiling):
                return v
    return 0.0


@lru_cache(maxsize=1)
def _load_division_map() -> dict:
    """district_name(normalised) -> division_name.

    Tries data/district_division.csv + data/divisions.csv first. If those
    files are not readable at runtime, falls back to the hardcoded map that
    mirrors them exactly.
    """
    try:
        dd = pd.read_csv(DISTRICT_DIVISION_PATH)
        dv = pd.read_csv(DIVISIONS_PATH)
        code_to_name = {
            str(c).strip(): str(n).strip()
            for c, n in zip(dv["division_code"], dv["division_name"])
        }
        m: dict = {}
        for _, row in dd.iterrows():
            dn = _norm_district(row["district_name"])
            code = str(row["division_code"]).strip()
            m[dn] = code_to_name.get(code, "unknown")
        return m
    except FileNotFoundError:
        # Hardcoded fallback equivalent to the two CSVs.
        return {
            _norm_district(k): _DIVISION_NAME_FALLBACK.get(v, "unknown")
            for k, v in _DISTRICT_CODE_TO_DIVISION_CODE_FALLBACK.items()
        }


def _division_map() -> dict:
    return _load_division_map()


def select_latest_per_facility(df: pd.DataFrame) -> pd.DataFrame:
    """Deduplicate submissions per facility, keeping the latest per key.

    If ``_validation_status`` is present, drop rows whose value is present
    and not "approved" (blank/missing kept).  Dedup key is
    (normalised facility_name, rp_end, _id); when _id is blank fall back to
    (normalised facility_name, rp_end, _submission_time).  Rows with the
    same name but different _id are never collapsed.  regional_dir is kept.
    """
    if df is None or df.empty:
        return df
    d = df.copy()

    if "_validation_status" in d.columns:
        vs = d["_validation_status"]
        mask = vs.notna() & (vs.astype(str).str.strip() != "") & (
            vs.astype(str).str.lower() != "approved"
        )
        d = d[~mask]

    d["_norm_name"] = d.get(
        "facility_name", pd.Series([""] * len(d), index=d.index)
    ).apply(_norm_name)

    rp_end_str = d.get("rp_end", pd.Series([""] * len(d), index=d.index)).astype(str)
    id_str = d.get("_id", pd.Series([""] * len(d), index=d.index)).astype(str).str.strip()
    st_str = d.get("_submission_time", pd.Series([""] * len(d), index=d.index)).astype(str)
    tail = id_str.where(id_str != "", st_str)
    d["_key"] = d["_norm_name"] + "\u0001" + rp_end_str + "\u0001" + tail

    d["_st"] = pd.to_datetime(
        d.get("_submission_time", pd.Series([None] * len(d), index=d.index)),
        errors="coerce",
    )
    idx = d.groupby("_key")["_st"].idxmax()
    d = d.loc[idx].drop(columns=["_norm_name", "_key", "_st"])
    return d.reset_index(drop=True)


def _has_numeric_direct(df: pd.DataFrame) -> bool:
    return "direct" in df.columns and pd.api.types.is_numeric_dtype(df["direct"])


def aggregate_reach(df: pd.DataFrame, family_factor: float = 5) -> dict:
    """Headline reach summary.

    Uses an existing numeric ``direct`` column as-is (never re-resolves);
    otherwise resolves per row via resolve_active.  Ignores rows whose
    source is "not_applicable" or whose direct is blank.
    """
    empty = {
        "direct": 0.0,
        "family": 0.0,
        "total": 0.0,
        "source_mix": {},
        "rows_resolved": 0,
        "rows_skipped": 0,
    }
    if df is None or len(df) == 0:
        return empty
    d = df.copy()
    direct_vals: list = []
    sources: list = []
    resolved = 0
    skipped = 0
    use_existing = _has_numeric_direct(d)
    if use_existing:
        direct_series = pd.to_numeric(d["direct"], errors="coerce")
        for i, row in d.iterrows():
            src = row.get("source", "")
            if pd.isna(src) or str(src).strip() == "not_applicable":
                skipped += 1
                continue
            dv = direct_series.loc[i]
            if pd.isna(dv):
                skipped += 1
                continue
            direct_vals.append(float(dv))
            sources.append(str(src).strip())
            resolved += 1
    else:
        for _, row in d.iterrows():
            r = resolve_active(row.to_dict())
            src = r.get("source", "")
            dv = r.get("direct")
            if src == "not_applicable" or dv is None:
                skipped += 1
                continue
            direct_vals.append(float(dv))
            sources.append(str(src))
            resolved += 1
    total_direct = sum(direct_vals)
    source_mix: dict = {}
    for s in sources:
        source_mix[s] = source_mix.get(s, 0) + 1
    return {
        "direct": total_direct,
        "family": total_direct * family_factor,
        "total": total_direct * (1 + family_factor),
        "source_mix": source_mix,
        "rows_resolved": resolved,
        "rows_skipped": skipped,
    }


def breakdown(df: pd.DataFrame, by: str) -> pd.DataFrame:
    """Break reach down by service / division / district.

    by in {"service", "division", "district"}.  Uses existing numeric
    ``direct`` column as-is; otherwise resolves per row.  Cumulative
    values above SANITY_CEILING are excluded from the sum.

    Returns a DataFrame with the group name in the ``group`` column.
    """
    if by not in ("service", "division", "district"):
        raise ValueError(f"unknown breakdown: {by}")
    if df is None or len(df) == 0:
        return pd.DataFrame(
            columns=[
                "group",
                "reports",
                "facilities",
                "direct",
                "family_x5",
                "total_reach",
                "new",
                "waiting",
                "cumulative",
                "source_mix",
            ]
        )
    d = df.copy()
    if by == "service":
        d = d[d.get("facility_type", pd.Series([""] * len(d), index=d.index)).astype(
            str
        ) != "regional_dir"].copy()
        group = d.get(
            "facility_type", pd.Series([""] * len(d), index=d.index)
        ).astype(str)
    elif by == "division":
        norm_district = d.get(
            "district", pd.Series([""] * len(d), index=d.index)
        ).apply(_norm_district)
        dmap = _division_map()
        group = norm_district.apply(lambda x: dmap.get(x, "unknown"))
    else:
        group = d.get(
            "district", pd.Series([""] * len(d), index=d.index)
        ).astype(str)

    if _has_numeric_direct(d):
        d["_direct"] = pd.to_numeric(d["direct"], errors="coerce").fillna(0.0)
        d["_source"] = d.get("source", pd.Series([""] * len(d), index=d.index)).astype(
            str
        )
    else:
        resolved = d.apply(lambda r: resolve_active(r.to_dict()), axis=1)
        d["_direct"] = [
            float(r.get("direct")) if r.get("direct") is not None else 0.0
            for r in resolved
        ]
        d["_source"] = [str(r.get("source", "")) for r in resolved]

    d["_new"] = d.apply(lambda r: _first_non_blank(r, NEW_FIELDS), axis=1)
    d["_waiting"] = d.apply(lambda r: _first_non_blank(r, WAITING_FIELDS), axis=1)
    d["_cumulative"] = d.apply(
        lambda r: _first_non_blank(r, CUM_FIELDS, ceiling=SANITY_CEILING), axis=1
    )

    d["_group"] = group.values
    out_rows = []
    for key, sub in d.groupby("_group", dropna=False):
        direct_sum = float(sub["_direct"].sum())
        source_mix: dict = {}
        for s in sub["_source"]:
            source_mix[s] = source_mix.get(s, 0) + 1
        names = sub.get(
            "facility_name", pd.Series([""] * len(sub), index=sub.index)
        ).apply(_norm_name)
        out_rows.append(
            {
                "group": key,
                "reports": int(len(sub)),
                "facilities": int(names[names != ""].nunique()),
                "direct": direct_sum,
                "family_x5": direct_sum * FAMILY_FACTOR,
                "total_reach": direct_sum * (1 + FAMILY_FACTOR),
                "new": float(sub["_new"].sum()),
                "waiting": float(sub["_waiting"].sum()),
                "cumulative": float(sub["_cumulative"].sum()),
                "source_mix": source_mix,
            }
        )
    out = pd.DataFrame(out_rows)
    if out.empty:
        return out
    return out.sort_values("direct", ascending=False).reset_index(drop=True)


def apply_sanity_ceiling(df: pd.DataFrame, ceiling: float = SANITY_CEILING) -> pd.DataFrame:
    """Add boolean ``implausible_value`` where any cumulative field exceeds ceiling."""
    d = df.copy()
    d["implausible_value"] = False
    for c in CUM_FIELDS:
        if c in d.columns:
            vals = pd.to_numeric(d[c], errors="coerce")
            d["implausible_value"] = d["implausible_value"] | (vals > ceiling)
    return d


# ---------------------------------------------------------------------------
# NEW: tiered totals for the Executive page and home strip
# ---------------------------------------------------------------------------

def _num_sum(series) -> float:
    """Safe numeric sum that tolerates Nones and NaNs."""
    return float(pd.to_numeric(series, errors="coerce").fillna(0.0).sum())


def _bucket_of(code: str) -> str:
    """Classify a facility_type code into Current / Lifetime / Registration."""
    if code in LIFETIME_TOTALS:
        return "Lifetime"
    if code in REGISTRATION_BODIES:
        return "Registration"
    return "Current"


def aggregate_totals(df: pd.DataFrame, family_factor: int = 5) -> dict:
    """Tiered totals for the Executive page and home strip.

    Returns:
      current_direct       Direct for current (non-lifetime, non-registration) services
      lifetime_direct      Direct for NOWPDP + Disability Certificates
      lifetime_nowpdp      Direct for NOWPDP alone
      lifetime_dis_cer     Direct for Disability Certificates alone
      registration_direct  Direct for SPDPA + regional_dir (should be ~0)
      combined_direct      current + lifetime (matches Dashboard!H24)
      indirect_reported    Facility-reported indirect reach
      waiting              Reported waiting-list total
      family_estimate      current_direct * family_factor
      total_reach_current  current_direct * (1 + family_factor)
      n_reports_current    Submissions in the current bucket
      n_reports_lifetime   Submissions in the lifetime bucket
      invalid_rows         Rows flagged source == 'invalid_value'
    """
    empty = {
        "current_direct": 0.0,
        "lifetime_direct": 0.0,
        "lifetime_nowpdp": 0.0,
        "lifetime_dis_cer": 0.0,
        "registration_direct": 0.0,
        "combined_direct": 0.0,
        "indirect_reported": 0.0,
        "waiting": 0.0,
        "family_estimate": 0.0,
        "total_reach_current": 0.0,
        "n_reports_current": 0,
        "n_reports_lifetime": 0,
        "invalid_rows": 0,
    }
    if df is None or len(df) == 0:
        return empty

    ft = df["facility_type"].astype(str)
    is_lifetime = ft.isin(LIFETIME_TOTALS)
    is_registration = ft.isin(REGISTRATION_BODIES)
    is_current = ~is_lifetime & ~is_registration

    direct_col = df["direct"] if "direct" in df.columns else pd.Series(0.0, index=df.index)

    current_direct = _num_sum(direct_col[is_current])
    lifetime_direct = _num_sum(direct_col[is_lifetime])
    lifetime_nowpdp = _num_sum(direct_col[ft == "nowpdp"])
    lifetime_dis_cer = _num_sum(direct_col[ft == "dis_cer"])
    registration_direct = _num_sum(direct_col[is_registration])

    # Reported indirect: try since-inception column first, else per-submission
    indirect_reported = 0.0
    for col in (
        "Total_Indirect_Reach_ablishment_Indirect",
        "Total_indirect_reach_since_inception",
    ):
        if col in df.columns:
            indirect_reported = _num_sum(df[col])
            if indirect_reported:
                break

    # Waiting: first available waiting column
    waiting = 0.0
    for col in ("c_waiting", "w_waiting", "waiting", "n_waiting"):
        if col in df.columns:
            waiting = _num_sum(df[col])
            if waiting:
                break

    invalid_rows = 0
    if "source" in df.columns:
        invalid_rows = int((df["source"].astype(str) == "invalid_value").sum())

    return {
        "current_direct": current_direct,
        "lifetime_direct": lifetime_direct,
        "lifetime_nowpdp": lifetime_nowpdp,
        "lifetime_dis_cer": lifetime_dis_cer,
        "registration_direct": registration_direct,
        "combined_direct": current_direct + lifetime_direct,
        "indirect_reported": indirect_reported,
        "waiting": waiting,
        "family_estimate": current_direct * family_factor,
        "total_reach_current": current_direct * (1 + family_factor),
        "n_reports_current": int(is_current.sum()),
        "n_reports_lifetime": int(is_lifetime.sum()),
        "invalid_rows": invalid_rows,
    }