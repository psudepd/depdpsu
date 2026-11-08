Phase 5: Programme dashboards, directory and pivot.

Read `docs/00_specification.md` Sections 8, 9 and 10, and `docs/field_dictionary.csv`.

Task: build the Partner Programs page (NOWPDP P1 to P5, C-ARTS V1 to V5, Deaf Reach, SIPMR, Inclusive Education), the Service Performance page, the Facility Directory and Profile (tabs listed in Section 8), and the Pivot and Reports page.
- Use the unit and aggregation rule columns of `field_dictionary.csv` for every metric. Never total across units.
- C-ARTS V5 parents are never added to the disability beneficiary total.
- Pivot aggregation follows the rule code (CUM, SNAP, FLOW).
- Exports: CSV, Excel pivot, chart PNG at 2x, management PDF.

Plan first, then wait for my approval.


Also build the Summary Reports tab (developer prompt section 4F): division, district and service-type update status with Direct / Indirect / Total, the district x service matrix, and the pending list. Reproduce tests/expected_summary_report.csv.

Also build the Summary Sheet (register) on the Summary Reports tab: service type, category, ownership class, region, district, organisation / institute name, period, Direct, Indirect, Total, with subtotals and a grand total. Reproduce `tests/expected_summary_sheet.csv`. Excel and JPG download on every table.
