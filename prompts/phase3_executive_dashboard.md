Phase 3: Executive dashboard and filters.

Read `docs/00_specification.md` Sections 3, 4, 5 and 8.

Task: build the Streamlit app shell with sidebar navigation (8 pages), the top filter bar, and the Executive Overview page.
- Cascading filters: Division, District, Facility, with the other independent filters from Section 4. Active-filter chips and Reset All. Child selections clear when the parent changes.
- One filtered dataframe feeds every number, chart and export.
- Eight KPI cards, trend, gender donut, service mix, division comparison, latest submission status.
- A banner "SYNTHETIC TEST DATA" whenever the synthetic file is the source.
- Responsive layout. Theme colours from `.streamlit/config.toml`.
- Show missing periods as missing, not zero. Show "Not applicable" and "Not collected" states.

- Add the breakdown tables by facility type, region (division) and district from `prompts/dashboard_developer_prompt_v2.md` Section 4A, reconciling to the grand total.

Plan first, then wait for my approval.


**Regional Director (`regional_dir`) is office information only:** exclude it from service lists, beneficiary totals and service counts; show it only in the admin Offices view and as a green dashed office marker. Add the Summary Reports tab described in prompts/dashboard_developer_prompt_v2.md section 4F.

Also show on the Executive page: Main total beneficiaries (Direct), Total indirect beneficiaries (Estimated), Total reach, Direct for each of the 18 services, and a Data received panel (developer prompt sections 4C and 4F).

Build the shared filter bar (service type, ownership class, region, district, facility, period, Active / Cumulative) used on every tab, and add Download Excel and Download JPG to every table using `src/export/exporters.py` (developer prompt section 4G).
