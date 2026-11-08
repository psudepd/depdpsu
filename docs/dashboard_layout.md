# Dashboard layout (wireframes)

Left sidebar: Executive Overview | Geographic Coverage | Beneficiaries & Gender | Service Performance | Partner Programs | Facility Directory | Pivot & Reports | Summary Reports | Data Quality
Top bar (all pages): Division > District > Facility, period (year / quarter / month), facility type, ownership, Active / Cumulative toggle, "Last refreshed hh:mm (Asia/Karachi)" with a "stale" badge when Kobo was unreachable, Refresh (admin only).

## 1. Executive Overview
```
[ Main total beneficiaries (Direct) ] [ Total indirect (Estimated, x5) ] [ Total reach (Estimated) ] [ Reported indirect reach (separate) ]
[ Reports ] [ Facilities ] [ Districts x/30 ] [ Divisions x/6 ] [ New ] [ Waiting ] [ Devices ]
[ Direct by service type (18 bars/cards) ............ ] [ Gender donut ] 
[ Division comparison (bar) ........................ ] [ Trend by period ]
[ Data received: last submission, source mix, latest 10 reports ]
```
## 2. Geographic Coverage
```
[ headline cards: Direct | Indirect | Total ]
[ MAP (neutral division tints, district outlines, markers: icon + ownership colour) ] [ Direct by service panel ]
[ Legend: ownership colours + icons + counts ]                                        [ Data received panel ]
[ Accessible table alternative (collapsible) ]
```
## 3. Beneficiaries & Gender
Reach summary, male / female / other (W reports only), tables by service, division, district (section 5.6 of the specification).
## 4. Service Performance / 5. Partner Programs
Indicator cards and charts by service with correct units; NOWPDP P1-P5, C-ARTS V1-V5, Deaf Reach T, SIPMR U, Inclusive N.
## 6. Facility Directory
Searchable table; click opens Overview | Beneficiaries | Services | Reporting history | Data quality | Map.
## 7. Pivot & Reports
Rows, columns, metric, aggregation per the metric dictionary; CSV / XLSX / PNG / PDF.
## 8. Summary Reports
Coverage strip; division table; district table with service chips; service table; district x service matrix; pending list (CSV).
## 9. Data Quality
Schema status of the Kobo export, unknown columns, W zero / copied / mismatch, all-zero, implausible values, same-name groups, ownership conflicts, misclassified types, missing coordinates, contact-field misuse.
