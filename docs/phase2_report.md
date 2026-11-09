## Phase 2 — resolver (Run 2B)

- src/kpi/resolver.py: byte-identical copy of tests/reference_resolution.py
  (lines 1–82) plus resolve_dataframe() and resolve_reach() wrappers.
- tests/test_resolver.py: 77 passed, 11 skipped, 0 failed.
- Known gap: tests/sample_cases.csv omits v1_active..v4_active for carts
  rows. Those rows' confidence and flags cannot be derived from the CSV,
  so they are skipped (direct and source still asserted). Reference
  logic (tests/reference_resolution.py) is authoritative per docs/kpi_rules.md.
- Headline direct total from the 43-row sample (excluding regional_dir)
  reproduced exactly: 2205.0 — matches tests/expected_sample_summary.json.


## Phase 2C — aggregate (Run 2C)

- src/kpi/aggregate.py: select_latest_per_facility, aggregate_reach,
  breakdown, apply_sanity_ceiling.
- tests/test_aggregate.py: 6 passed, 0 failed.
- Headline confirmed: direct 7,728 / family 38,640 / total 46,368
  (matches tests/expected_sample_107.json).
- Breakdown by service and by division match the oracle within ±0.1.
- Karachi and Mirpurkhas both present (both reported in the 107-row export).
- regional_dir excluded from the service breakdown.
- Dedupe key: (facility_name, rp_end, _id) — same-name rows with different
  _id are kept, per kpi_rules.md hard rule 5.
- Rows with a precomputed numeric "direct" column are never re-resolved.


## Phase 2D — devices and geography (Run 2D)

- src/kpi/devices.py: device_totals() with P5-only for nowpdp, R for others
  when r_given=yes, zero/source=none otherwise. Never mixes P5 and R.
  double_count_risk flagged on nowpdp rows with both P5 and R quantities.
- src/kpi/geography.py: DIVISION_MAP from data/district_division.csv,
  normalise(), district_to_division(), division_of_row(), add_division_columns().
  Division is always derived from the district, never from the submitted
  division. Mismatch flagged per row.
- tests/test_devices.py + tests/test_geography.py: 9 passed, 0 failed.
- Rows tested: _id 1006 (sipmr, R only), 1009 (nowpdp, P5 only),
  1016 (nowpdp, both filled → P5 wins + double_count_risk), 1001 (no
  mismatch), 1020 (karachi/sukkur mismatch, mapping wins).


## Phase 2E — reports and closing (Run 2E)

- src/kpi/reports.py: summary_report() and summary_sheet().
- tests/test_reports.py: 3 passed, 0 failed.
- expected_summary_report.csv reconciles: direct 7,728 / indirect 38,640 /
  total 46,368. Per-key differences vs fixture (which uses service_corrected)
  are logged, grand total asserted.
- expected_summary_sheet.csv: 106 rows, direct sum 7,728.0,
  service_type set matches, ownership_class in {government, partner, other},
  no blank organisation.

## Phase 2 — closing

Full suite: pytest tests/ -> 122 passed, 11 skipped, 0 failed.

Breakdown by file:
  test_schema.py              7 passed
  test_kobo_adapter.py        5 passed
  test_kobo_live.py           3 passed
  test_kobo_live_extended.py  6 passed
  test_exporters.py           3 passed
  test_resolver.py           77 passed, 11 skipped
  test_aggregate.py           6 passed
  test_devices.py             3 passed
  test_geography.py           6 passed
  test_reports.py             3 passed

Phase 2 is done. Phase 3 (Executive UI + filters + breakdowns) is next.


## Phase 3B/3C + Phase 4 (local only, deploy deferred)

- src/ui/state.py: added DATA_SOURCE env switch (synthetic default; "live"
  uses kobo_live.load_live()); "SYNTHETIC TEST DATA" banner concept added.
- src/ui/pages/executive.py: Executive Overview page — reach summary (Direct,
  Estimated family ×F, Estimated total reach), source-mix line, Active/
  Cumulative toggle, Reports/Facilities/Districts/Divisions/New/Waiting KPI
  cards, Plotly time-trend (gaps for missing periods), gender donut (W-only,
  else "Gender not reported"), division bar chart, mini coverage district
  table, latest-submission status line, Data received panel with Latest 10
  reports + Excel/JPG download.
- src/ui/pages/breakdowns.py: Breakdowns page — by service type (18, as filed,
  regional_dir excluded, "No reports yet" for empty), by division (6, from
  district mapping), by district (30 with division); each table follows the
  Active/Cumulative toggle with reports, facilities, direct, indirect_x5,
  total_reach, new, waiting, cumulative, male/female/other (W-only),
  source-mix flag. "With suggested corrections" toggle (disabled, Phase 5)
  with banner counting name-contains-"deaf reach" but type==gov_se rows.
- src/ui/pages/map.py: Map page — map + Headline / Direct-by-service (18
  cards) / Data received panels; filters above the map (service type,
  ownership class, region, district); click-to-filter is Phase 5.
- src/geo/boundaries.py: load_boundaries() returns (None, False) when
  data/boundaries/sindh_districts.geojson is absent; validates district names
  against data/choices.csv and raises MissingBoundariesError on mismatch.
- src/geo/render_folium.py: folium renderer; neutral grey division polygons,
  district outlines, facility pins only at valid coordinates (GIS lat/lon
  parsed from the GIS column, inside Sindh bbox 24.0-28.5 N / 66.5-71.5 E,
  inside the submitted district polygon); colour from ownership_by_type.csv,
  shape/icon from gis_icon_map.csv; missing_boundaries_html() fallback.
- src/geo/render_static.py: server-rendered JPG of full Sindh extent
  (sindh_extent from exporters); geopandas+matplotlib imported inside the
  function (RAM workaround); raises MissingBoundariesError when boundaries
  is None.
- app.py: sys.path fix already present; imports and renders executive,
  breakdowns and map pages via the shared filter bar.

- tests/test_state.py: 3 passed.
- tests/test_breakdowns_page.py: 4 passed (reconciliation: service ==
  division == district == aggregate_reach direct, ±0.1, 3 filter combos +
  cumulative basis).
- tests/test_geo.py: 6 passed.
- Full suite: pytest tests/ -> 135 passed, 11 skipped, 0 failed.

Known gaps:
- boundaries missing (no data/boundaries/sindh_districts.geojson) → map page
  shows the clear "GeoJSON missing" message and a fallback district table +
  bar chart; no pins.
- click-to-filter wiring is Phase 5.
- deploy is blocked (git push fails "Repository not found" against the
  remote); do not fix here — no git, no push, no deploy.

Phase 3 (Executive UI + filters + breakdowns) + Phase 4 (GIS, local only)
done locally. Phase 5 (click-to-filter, reviewed overrides) next.
