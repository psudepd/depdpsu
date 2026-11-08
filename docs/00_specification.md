**DEPD Executive Analytics & GIS Dashboard**

**Final Development Specification**

Version 1.3 (Final) \| Supersedes Version 1.2 \| Ready for Antigravity / Streamlit development

Government of Sindh — Department of Empowerment of Persons with Disabilities (DEPD)

| **Source schema**                                                                                                                                                                                                                                                                                  | **Business definitions**                                | **Status**                                                                                                                               |
|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------|
| Kobo XLSForm shared 4 Nov 2026 (id_string: depd_beneficiary_data_v6; 296 survey rows, 215 choices). The 7 Nov export has 1,510 columns, so the live form is newer: re-share it (decision 26) and a 107-row real sample export (1 to 7 Nov 2026). Live source: Kobo export-settings API (Section 9) | DEPD Beneficiary Data Collection Form, Version 7 (Word) | Final for development. Beneficiary rules: 5.3 to 5.5. Summary Reports: 5.7. Map: Section 7. Live data and deployment: Sections 9 and 12. |

# 1. Executive objective

Build a secure, responsive, visually polished, live Streamlit executive dashboard for aggregate beneficiary and service reporting by DEPD facilities and partner organisations. The latest Kobo XLSForm is the exact technical schema, and the sample export shows how users really fill it. The Version 7 Word form is the business-definition reference. This document specifies the dashboard only; it does not change or redeploy the Kobo form.

**Out of scope:** individual beneficiary records, cross-facility person-level deduplication, financial or grant spending analysis, and any change to the Kobo form.

# 2. Source audit (verified against the latest XLSForm and the sample export)

| **Finding**                        | **Observed result**                                                                                                                                                                                                                                                                                                 | **Implementation consequence**                                                                                                                                    |
|------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Workbook structure**             | survey: 296 rows (header excluded), 33 groups, 143 integer fields, 29 multi-select questions, 1 calculation. choices: 215 rows. No repeat groups.                                                                                                                                                                   | One submission = one flat row = one facility for one reporting period.                                                                                            |
| **Form identity**                  | settings: id_string = depd_beneficiary_data_v6, version = 7.0.                                                                                                                                                                                                                                                      | Use the deployed asset UID, not the document title. Store form version with every row.                                                                            |
| **Geography**                      | 6 divisions and 30 districts. Fields division and district; district is filtered by division in the form.                                                                                                                                                                                                           | Join district to division from the choice list. Flag any mismatch (Section 11).                                                                                   |
| **Facility identity**              | facility_name is free text. facility_type has 19 choices (Section 6), including the new gia, sindh_persons_with_disabilitie, dis_cer and legal_support\_\_beneficiaries.                                                                                                                                            | Create a governed facility registry with stable IDs and alias matching. Never rely on names alone.                                                                |
| **Geolocation**                    | The form has one geopoint question named GIS in Section A. It is now required (41 of 43 sample reports have a value; Kobo also exports \_GIS_latitude and \_GIS_longitude). It is officer-reported and unverified.                                                                                                  | Use registry coordinates first. Use reported GIS as "Reported, not yet verified" only after the checks in Section 7.                                              |
| **Headline headcounts**            | w_male, w_female, w_trans, w_other, w_total (calculation), w_new, w_waiting. Section W is hidden for pcrdp, assistive_ip and regional_dir.                                                                                                                                                                          | pcrdp and regional_dir are excluded from beneficiary KPIs ("Not applicable"); assistive_ip uses its device recipients (5.3, decision 23).                         |
| **Section W reliability (sample)** | In 43 real reports: 3 have W = 0 while their section holds real active figures; 2 copied the cumulative total into W (W 607 vs c_active 78; W 422 vs 65); 7 differ from the section figure by more than 20%; 3 are all zero.                                                                                        | Never sum w_total alone. Resolve Direct beneficiaries with the ladder in Section 5.3.                                                                             |
| **Indirect reach fields**          | New: Total_indirect_reach_since_inception (Section C), Beneficiary_students_inception_In_Direct (Deaf Reach), Total_Indirect_Reach_ablishment_Indirect (legal support).                                                                                                                                             | Reported indirect reach is separate from the family estimate (Section 5.5).                                                                                       |
| **New facility types and groups**  | gia (Grant-in-Aid), sindh_persons_with_disabilitie (SPDPA), dis_cer (Issuing District, disability certificates), legal_support\_\_beneficiaries (Access to Justice). New groups: disability certificate (G1C) and legal support (G2). New question Who_is_the_primary_r_d_materials_services (Outreach / Internal). | Added to routing (Section 6) and the metric dictionary (Appendix A).                                                                                              |
| **Sample data quality**            | 12 "DEPD Digital Classes Deaf Reach" reports are filed as gov_se; facility names are free text with spelling variants; contact_name and officer_designation sometimes hold a phone number or 0; no report has a Kobo validation status yet.                                                                         | Diagnostics in Section 11.3. Never auto-correct stored values.                                                                                                    |
| **New / waiting coverage**         | w_new and w_waiting are asked only for deaf_reach, sipmr, carts, hostel, vtc, academy, ipmr and nowpdp. rcmhc, rcph and gov_se use c_new and c_waiting. inclusive uses n_new and n_waiting.                                                                                                                         | Use the canonical coalesce rules in Section 5. A KPI built on w_new alone would miss five facility types.                                                         |
| **Age and disability coverage**    | w_age_groups (6 choices) and w_disability are multi-select.                                                                                                                                                                                                                                                         | Coverage only. Never chart them as population distributions.                                                                                                      |
| **Reporting period**               | rp_start is now labelled "Since Date of Center/Institution Inception" and rp_end is the report date. 8 of 43 sample reports have rp_start equal to rp_end. There is no quarter or month field.                                                                                                                      | Use rp_end only for the period (year, quarter, month). Treat rp_start as the facility inception date. Cadence is unconfirmed (Section 14).                        |
| **Verification**                   | Two different things: form field verification_status (verified / not_verified, set by the reporting side) and Kobo \_validation_status (set by reviewers in Kobo).                                                                                                                                                  | Treat a row as accepted only when Kobo \_validation_status is Approved, if the review workflow is used. Show both statuses separately.                            |
| **Assistive devices**              | Section R is shown to all facility types, including NOWPDP. NOWPDP also reports devices in P5.                                                                                                                                                                                                                      | Real double-count risk. One canonical source per submission (Section 5.2).                                                                                        |
| **Personal / sensitive fields**    | contact_name, contact_info, signature (image), s_pic_1 to s_pic_5 (images), s_story_file (PDF).                                                                                                                                                                                                                     | Access-controlled. Never shown on public or viewer pages (Section 11).                                                                                            |
| **Document discrepancy**           | The V7 Word document header still says "Version 5".                                                                                                                                                                                                                                                                 | Confirm the canonical version name before publication.                                                                                                            |
| **Regional Director**              | regional_dir holds office information only (Sections A and B). The office manages several services and has no beneficiaries of its own.                                                                                                                                                                             | Not a service. Excluded from service lists, totals, breakdowns and service counts. Shown only in an admin Offices view and as a green dashed office marker (7.1). |
| **Ownership vs type**              | In the 107-row export, 37 of 58 gov_se reports say ownership = partner (mostly the "DEPD Digital Classes Deaf Reach" centres); Deaf Reach is mostly "other"; C-ARTS is government in all 5.                                                                                                                         | Ownership is self-declared and unreliable. Colour by the DEPD class of the service type; the submitted value is a check (7.1).                                    |
| **Implausible values**             | One RCMHC report has a cumulative value of 3.37e215.                                                                                                                                                                                                                                                                | Sanity ceiling per field (default 1,000,000, admin setting): exclude from sums and flag "implausible value".                                                      |
| **Data availability**              | The XLSForm holds schema only. Submissions arrive through the Kobo export-settings API (Section 9).                                                                                                                                                                                                                 | The app reads live data through a cache. Synthetic fixtures are used only for tests and are labelled.                                                             |

# 3. Dashboard architecture and layout

**Visual style:** modern executive government analytics. Navy \#18345A, teal \#008C95, white \#FFFFFF, slate \#66758C. Wide desktop layout, responsive tablet and mobile layout, left sidebar navigation and a compact top filter bar. DEPD and Sindh government logos only if approved assets are supplied.

| **Page**                            | **Required features**                                                                                                                                                                                                                                                                                                                    |
|-------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **1. Executive Overview**           | Reach summary block (Direct, Estimated family, Estimated total; Active / Cumulative toggle; Section 5.3 to 5.5), then reporting facilities, coverage %, new, waiting, reported indirect reach and devices distributed. Also time trends, gender donut, service mix, division comparison, mini coverage map and latest-submission status. |
| **2. Geographic Coverage**          | Neutral division polygons, district boundaries, district choropleth, facility pins coloured by ownership (green government, blue partner organisation, purple other) with service icons (Section 7), the headline and service panels and the Data received panel (7.4).                                                                  |
| **3. Beneficiaries & Gender**       | Reach summary; unique active, new and waiting; male / female / transgender / other; trends; breakdown tables by facility type, region (division) and district (Section 5.6). Age and disability coverage only.                                                                                                                           |
| **4. Service Performance**          | Education, rehabilitation and health, training, employment, assistive devices, identity facilitation, residential. Correct units for each indicator (Appendix A).                                                                                                                                                                        |
| **5. Partner Programs**             | NOWPDP P1 to P5, C-ARTS V1 to V5, Deaf Reach (T), SIPMR (U), Inclusive Education (N). Drill-down to programme KPIs.                                                                                                                                                                                                                      |
| **6. Facility Directory & Profile** | Searchable facilities with status, district, services, reporting history, completeness, aggregate metrics and map point. Detail tabs in Section 8.                                                                                                                                                                                       |
| **7. Pivot & Reports**              | Group by division / district / facility / service / period, metric selector, valid aggregation per the metric dictionary, CSV / XLSX, PNG and PDF export.                                                                                                                                                                                |
| **8. Summary Reports**              | Which divisions, districts and service types have updated data; the Summary Sheet listing every service with region, district, organisation name and beneficiaries; district x service matrix; pending list; Excel and JPG downloads (Section 5.7).                                                                                      |
| **9. Data Quality & Diagnostics**   | Coverage denominators, late and missing reports, missing coordinates, region-district mismatch, duplicates, anomalies, API sync status.                                                                                                                                                                                                  |

# 4. Global cascading filters (mandatory)

- **Hierarchy:** Division → District → Facility. Start at All Sindh / All Districts / All Facilities. A division limits districts and facilities. A district limits facilities. Child selections are cleared when the parent changes.

- **Independent filters:** reporting year, quarter / month or date range; service type (multi-select); ownership class (Government / Partner organisation / Other); facility type; service category; programme (NOWPDP P1 to P5, C-ARTS V1 to V5); ownership; operational status (op_status); Kobo validation status; form verification status.

- **The same filter bar is on every tab, including the map:** service type, ownership class (government / partner organisation / other), region (division), district and facility, plus period and the Active / Cumulative toggle. Changing a filter on one tab keeps it on the others until Reset All.

- **One filtered dataset.** Every filter updates KPIs, map layers, charts, pivots, exports and facility cards from the same canonical filtered dataframe. Show active-filter chips and a Reset All button.

- **Multi-select** for comparisons, with an optional single-selection drill-down mode.

- **Selected-period logic:** snapshot indicators use the latest valid submission per facility in the selection. Flow indicators sum over distinct reporting periods (by rp_end). Cumulative indicators use the latest snapshot per facility and are never summed across periods. Use the Asia/Karachi time zone for all period boundaries.

- **Labelling:** totals across facilities are labelled "sum of facility-reported unique headcounts". Person-level deduplication across facilities is not possible from aggregate data.

# 5. KPI definitions and reporting semantics

## 5.1 Canonical KPIs

| **KPI**                           | **Source fields**                                                                                                                              | **Aggregation rule**                                                                                                                                                      |
|-----------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Reporting facilities**          | Registry facility_id with an accepted submission                                                                                               | Distinct count for the selected period. Without a registry, use matched names and label the result "unverified".                                                          |
| **Expected facilities**           | External approved facility registry                                                                                                            | If unavailable, show "coverage denominator unavailable".                                                                                                                  |
| **Reporting coverage %**          | Reporting ÷ expected eligible facilities × 100                                                                                                 | Show only when a denominator exists.                                                                                                                                      |
| **Direct beneficiaries (Active)** | Resolved per Section 5.3 (w_total first, then the section figure)                                                                              | Latest valid submission per facility; sum across facilities. Never add snapshots across time. Not a plain sum of w_total.                                                 |
| **Indirect (family) estimate**    | Direct x F, F = 5                                                                                                                              | Model estimate, always labelled "Estimated". Section 5.4.                                                                                                                 |
| **Total reach**                   | Direct + Indirect = Direct x (1 + F)                                                                                                           | Always labelled "Estimated". Section 5.4.                                                                                                                                 |
| **Reported indirect reach**       | Total_indirect_reach_since_inception, Beneficiary_students_inception_In_Direct, Total_Indirect_Reach_ablishment_Indirect                       | Cumulative; separate card; never added to the three numbers above (Section 5.5).                                                                                          |
| **New beneficiaries**             | coalesce(w_new, c_new, n_new)                                                                                                                  | Sum over distinct reporting periods (by rp_end).                                                                                                                          |
| **Waiting list**                  | coalesce(w_waiting, c_waiting, n_waiting)                                                                                                      | Latest snapshot per facility. Label "facility-reported, possible cross-facility overlap".                                                                                 |
| **Cumulative served**             | coalesce(c_cumulative, n_integrated, t_cum, u_cum, p_cum, Total_Direct_Benefic_since_establishment, Cumulative_Disabilit_sued_Since_Inception) | Latest snapshot per facility. Not collected for hostel, vtc, academy, ipmr or carts (V1 to V5 overlap): show "Not collected". Used by the Cumulative basis (Section 5.3). |
| **Gender**                        | w_male, w_female, w_trans, w_other                                                                                                             | Latest snapshot per facility, used only when W passed the check in 5.3 (otherwise "Gender not reported"), then sum over the filtered scope.                               |
| **Devices distributed**           | Section 5.2 mapping                                                                                                                            | Distributed quantities only. Never add Section U manufacturing counts.                                                                                                    |
| **Service outputs**               | Appendix A, unit column                                                                                                                        | Keep people, sessions, visits, devices, items, km/day, schools, cases and audits separate. Never total across units.                                                      |

## 5.2 Device mapping (one canonical source per submission)

| **Canonical device**                                       | **Section R field(s)** | **NOWPDP P5 field(s)** |
|------------------------------------------------------------|------------------------|------------------------|
| **Wheelchairs**                                            | r_wheelchair           | p5_wheelchair          |
| **Crutches, sticks, walkers**                              | r_crutches + r_walker  | p5_crutches            |
| **Motorised tri-wheelers**                                 | (not collected)        | p5_tricycle            |
| **Prosthetic limbs**                                       | r_limb                 | (not collected)        |
| **Orthoses**                                               | r_orthosis             | (not collected)        |
| **Hearing aids**                                           | r_hearing              | p5_hearing             |
| **Vision aids (spectacles, low-vision aids, white canes)** | r_spectacles           | p5_cane                |
| **Other devices**                                          | r_dev_other            | p5_other               |

- **Rule:** for a nowpdp submission use P5 quantities. For every other facility type use Section R quantities when r_given = yes. Never add the two.

- **Flag** "device double-count risk" when a nowpdp submission has r_given = yes and any R quantity above zero. Use P5 only until a reviewer resolves it.

- **Recipients** (r_male, r_female, r_trans, r_other and p5_cum / p5_fitted) are people. Devices are quantities. Never mix them. Section U fields (u_prosth_made, u_orth_made, u_repaired) are workshop output and stay in a separate measure.

## 5.3 Direct beneficiaries: resolving each submission

Many facilities leave Section W empty, type 0, or copy the cumulative total into it, and enter the real numbers in their own section. The dashboard therefore resolves one Direct figure per submission, with a recorded source and confidence. Reference code: tests/reference_resolution.py.

**Inputs:** W = w_total; S = the section-level active figure for the facility type (table below); C = the cumulative figure.

| **Step** | **Condition**                                                                | **Result**                                                                                                                                                                             |
|----------|------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **1**    | Facility type is pcrdp or regional_dir (office only, not a service)          | Not applicable (not 0). assistive_ip has no W: its Direct is the people who received devices in the period (R male + female + transgender + other), flagged "period count, not stock". |
| **2**    | W above 0 and W is not a copy of C (W equals C while S exists and S differs) | Use W (source "W"). If S above 0 and W differs from S by more than 20%, keep W and flag "review" (show both).                                                                          |
| **3**    | Otherwise S above 0                                                          | Use S (source "section"). Flag W_blank, W_zero or W_copied_from_cumulative.                                                                                                            |
| **4**    | Otherwise W = 0 or S = 0                                                     | Direct = 0, flag all_zero_report (low confidence). Never silently dropped.                                                                                                             |
| **5**    | Otherwise                                                                    | No data.                                                                                                                                                                               |

| **facility_type**                           | **S (section active figure)**                                                             | **C (cumulative figure)**                 |
|---------------------------------------------|-------------------------------------------------------------------------------------------|-------------------------------------------|
| **rcmhc, rcph, gov_se, gia, pcrdp**         | c_active                                                                                  | c_cumulative                              |
| **inclusive**                               | n_enrolled                                                                                | n_integrated                              |
| **carts**                                   | Largest of v1_active to v4_active (lower bound, low confidence). V5 parents are excluded. | none                                      |
| **nowpdp**                                  | Largest of p2_active, p3_active (lower bound, low confidence)                             | p_cum                                     |
| **deaf_reach**                              | none                                                                                      | t_cum                                     |
| **sipmr**                                   | none                                                                                      | u_cum                                     |
| **dis_cer, sindh_persons_with_disabilitie** | none                                                                                      | Cumulative_Disabilit_sued_Since_Inception |
| **legal_support\_\_beneficiaries**          | none                                                                                      | Total_Direct_Benefic_since_establishment  |
| **hostel, vtc, academy, ipmr**              | none                                                                                      | none (show "Not collected")               |

- **Basis toggle:** Active (default) uses the steps above. Cumulative uses C only (first non-blank); W is never used there. Dis_cer, SPDPA and legal-support facilities appear on the Cumulative basis.

- **Aggregation:** latest valid submission per facility and period (facility_id + rp_end); Direct per facility, then summed across facilities. Label totals "sum of facility-reported unique headcounts".

- **Transparency:** under each card show the source mix (for example "34 facilities from Section W, 5 from section data, 3 zero reports, 7 need review"). Clicking opens the facility list with W, S, the resolved value, the source and the flags.

- **Worked check:** on the 43 sample reports (before de-duplication) a plain sum of w_total gives 2,882, but the resolved Direct total is 2,205 (5 reports resolved from section data, 3 all-zero, 7 flagged for review). Family estimate 11,025; total reach 13,230. Expected values are in tests/expected_sample_summary.json.

## 5.4 Indirect (family) estimate and total reach

| **Number**                          | **Formula**                          | **Label**                  |
|-------------------------------------|--------------------------------------|----------------------------|
| **Direct beneficiaries**            | Resolved unique persons (5.3)        | Direct (facility-reported) |
| **Indirect (family) beneficiaries** | Direct x F, F = 5                    | Estimated, Direct x 5      |
| **Total reach**                     | Direct + Indirect = Direct x (1 + F) | Estimated total reach      |

- F is an admin-only setting (default 5). Show F in the card tooltip and in every export.

- The family estimate is a model, not a count. The word "Estimated" must appear wherever it or the total is shown. Never present it as reported data.

- Not part of Direct, and therefore not multiplied: C-ARTS V5 parent trainees, and any device, session, visit, case or certificate count.

## 5.5 Reported indirect reach (separate)

Facilities also report indirect reach themselves (outreach and community): Total_indirect_reach_since_inception, Beneficiary_students_inception_In_Direct and Total_Indirect_Reach_ablishment_Indirect. This is a different measure from the family estimate. Show it as its own cumulative card. Never add it to Direct, to the family estimate or to Total reach, because the two can describe the same people. The Outreach / Internal answer to Who_is_the_primary_r_d_materials_services is reported separately; Internal recipients are already inside the facility's own count and are never added to Direct.

## 5.6 Breakdown by facility type, region and district

Executives need the same numbers cut three ways. Provide three breakdown tables, each reconciling to the grand total, with the Active / Cumulative toggle and the Reach summary (5.3 to 5.5).

| **View**                       | **Grouped by**                                                     | **Rules**                                                                                                                                                                                                                                                                                                                           |
|--------------------------------|--------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **By facility type (service)** | facility_type as filed; optional "with suggested corrections" view | Default is "as filed". A banner shows the number of suggested corrections (for example 12 Deaf Reach reports filed as gov_se). The corrected view uses only reviewed overrides, never name matching alone. List all 18 service types (regional_dir is office information only), including those with no reports ("No reports yet"). |
| **By region (division)**       | Division derived from the district using the 30-district list      | Never use the submitted division field for totals (flag mismatches). Always list all 6 divisions; a division with no reports shows "No reports", not 0.                                                                                                                                                                             |
| **By district**                | district                                                           | Always list all 30 districts with their division. Click a district to set the global filter. Districts with no reports are greyed "No report".                                                                                                                                                                                      |

**Columns in every breakdown table:** reports, facilities (distinct), Direct, Indirect (family, Estimated), Total reach (Estimated), new, waiting, cumulative, male / female / other (only from reports where W was usable), and a source-mix flag (how many rows used W, the section figure, zero reports or are flagged for review).

- **Cross views:** service x division heatmap of Direct, and division -\> district -\> facility drill-down.

- **Reconciliation:** the rows of each table must add up to the grand total of the Reach summary under the same filters. Add a test for this.

- **Sort and share:** sortable columns and a share-of-total column; blank and zero stay different.

- **Reference results:** tests/expected_sample_107.json gives the expected numbers for the current 107-row export (regional_dir excluded: 106 service reports, 27 of 30 districts, all 6 divisions): Direct 7,728; Indirect (x5) 38,640; Total 46,368. By division: Sukkur 2,086; Hyderabad 2,066; Karachi 1,991; Shaheed Benazirabad 864; Larkana 607; Mirpurkhas 114. tests/expected_breakdown.csv is the older 43-row sample.

## 5.7 Summary Reports tab: who has updated data

One tab answers "which region, district and service types have updated data, and how many beneficiaries". It follows the global filters, the reporting period (rp_end, not submission time) and the Active / Cumulative toggle. Regional Director offices are excluded.

| **Block**                    | **Content**                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
|------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Coverage strip**           | Divisions updated x of 6; districts updated x of 30; service types updated x of 18; facilities reporting; reports received; last submission (Asia/Karachi).                                                                                                                                                                                                                                                                                                                        |
| **Division table**           | All 6 divisions: status (Updated / No report), districts and services updated, reports, Direct, Indirect (Estimated), Total reach (Estimated), last update.                                                                                                                                                                                                                                                                                                                        |
| **District table**           | All 30 districts with division, status, service types that reported (icon chips), reports, Direct, Indirect, Total, last update. "No report" rows stay visible in grey.                                                                                                                                                                                                                                                                                                            |
| **Service-type table**       | All 18 services: status, divisions and districts covered, reports, Direct, Indirect, Total, new, waiting.                                                                                                                                                                                                                                                                                                                                                                          |
| **Matrix**                   | District (rows) x service type (columns); cell = Direct; "-" = no report; toggle to report counts.                                                                                                                                                                                                                                                                                                                                                                                 |
| **Pending list**             | Districts and services with no report in the period; CSV export for follow-up.                                                                                                                                                                                                                                                                                                                                                                                                     |
| **Summary Sheet (register)** | One row per service report: Service type, Service category, Ownership class, Region (division), District, Organisation / institute name, Reporting period, Direct, Indirect (Estimated), Total reach (Estimated), Source flag. Sorted by service type, then region, then district, with a subtotal per service type and a grand total. The organisation name is facility_name (for assistive_ip the partner name in r_org). Institution names only: no contact or personal fields. |

- Every table reconciles to the grand total and has Download Excel and Download JPG buttons (Section 8). Reference: tests/expected_summary_report.csv and tests/expected_summary_sheet.csv (106 rows; government 76 reports, 4,803 Direct; partner 30 reports, 2,925 Direct).

# 6. Facility types, routing and service categories

The form has 19 facility types; 18 are services and regional_dir is office information only. Derive service-category flags from the union of the facility_type default, services_available, carts_services and nowpdp_programs. Use the facility-type default alone when the others are empty.

| **facility_type**                  | **Service category (map icon)**                                                    | **Sections shown in the form**                                        |
|------------------------------------|------------------------------------------------------------------------------------|-----------------------------------------------------------------------|
| **rcmhc**                          | Rehabilitation and education (multi-service)                                       | C, R, W                                                               |
| **rcph**                           | Rehabilitation (medical cross)                                                     | C, R, W                                                               |
| **gov_se**                         | Education / school (school building); subtype recorded in M                        | C, M, R, W                                                            |
| **inclusive**                      | Education (book)                                                                   | N, R, W                                                               |
| **deaf_reach**                     | Education / school (school building)                                               | T, R, W                                                               |
| **sipmr**                          | Health and rehabilitation; assistive devices                                       | L, U, R, W                                                            |
| **ipmr**                           | Health and rehabilitation (medical cross)                                          | L, R, W                                                               |
| **carts**                          | Training and therapy, multi-service (tools)                                        | V1 to V5 as selected, Q if partner support, R, W                      |
| **nowpdp**                         | Multi-service (layered icon); identity, education, vocational, employment, devices | P0 to P5 as selected, W (R discouraged, see 5.2)                      |
| **hostel**                         | Hostel / residential (bed)                                                         | I, R, W                                                               |
| **vtc**                            | Vocational (tools)                                                                 | K, R, W                                                               |
| **academy**                        | Teacher training (graduation cap)                                                  | H, R, W                                                               |
| **gia**                            | Grant-in-Aid, inclusive education (book with hand)                                 | C, H, I, K, L, M, N, R, W                                             |
| **sindh_persons_with_disabilitie** | Registration, complaints and certificates (identity card)                          | G1 (+ certificate group if ticked), R, W (W shown: decision 14)       |
| **dis_cer**                        | Disability certificates (identity card)                                            | Certificate group, R, W (W shown: decision 14)                        |
| **legal_support\_\_beneficiaries** | Legal support, Access to Justice (identity card)                                   | Legal support group, R, W (W shown: decision 14)                      |
| **pcrdp**                          | Registration (identity card). Legacy type.                                         | C, R. No Section W and no G1 (G1 now belongs to SPDPA: decision 16).  |
| **assistive_ip**                   | Assistive devices (wheelchair)                                                     | R only. No Section W.                                                 |
| **regional_dir**                   | Office information only (not a service). Green dashed office marker.               | A and B only. No beneficiary counts. Excluded from all service views. |

# 7. Sindh GIS specification

Use authoritative, licensed Sindh district boundary GeoJSON or shapefiles (30 districts) and derived division boundaries. Validate administrative names against the XLSForm choices. Never fabricate polygons.

## 7.1 Marker colour (ownership class), shape (service category) and icon (service)

**Colour = ownership class, fixed by service type** (rule from DEPD, data/ownership_by_type.csv). The submitted ownership field is only a check.

| **Class**                | **Colour** | **Hex**  | **Service types**                                                                                                                                              |
|--------------------------|------------|----------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Government**           | Green      | \#2E7D32 | RCMHC, RCPH, government special education, C-ARTS, vocational training centre, SPDPA, disability certificate (dis_cer), inclusive education, Regional Director |
| **Partner organisation** | Blue       | \#1F5FBF | Assistive devices, GIA, Deaf Reach                                                                                                                             |
| **Other**                | Purple     | \#7B3FA0 | Remaining types: SIPMR, IPMR, hostel, academy, NOWPDP, PCRDP, legal support (proposed; to confirm)                                                             |
| **Unknown**              | Grey       | \#6B7280 | Facility type missing or not in the table                                                                                                                      |

**Shape = service category**, so health, education and training differ even without colour:

| **Category**                                                                   | **Shape**              | **Icon inside**                                                              |
|--------------------------------------------------------------------------------|------------------------|------------------------------------------------------------------------------|
| **Health / rehabilitation (RCMHC, RCPH, SIPMR, IPMR)**                         | Circle                 | Medical cross                                                                |
| **Education / school (gov_se, inclusive, Deaf Reach, GIA)**                    | Rounded square         | School building (gov_se, Deaf Reach), book (inclusive), book with hand (GIA) |
| **Training / vocational (C-ARTS, VTC, Academy, NOWPDP)**                       | Hexagon                | Tools (C-ARTS, VTC), graduation cap (Academy), briefcase (NOWPDP)            |
| **Hostel / residential**                                                       | House (pentagon)       | Bed                                                                          |
| **Assistive devices**                                                          | Triangle               | Wheelchair                                                                   |
| **Registration / legal (SPDPA, disability certificate, legal support, PCRDP)** | Diamond                | Identity card, scales                                                        |
| **Regional Director (office, not a service)**                                  | Square, dashed outline | Office building                                                              |

Shape, icon, colour and a text label are always shown together, and the legend lists all four. A multi-service facility keeps its primary shape and adds a small badge. Division polygons use neutral grey tints (#EEF1F4 and \#E3E8ED) with dark outlines, so green, blue and purple belong to ownership alone. Check icon contrast (at least 4.5:1) and test the colours with a colour-vision simulator.

**Submitted ownership is a check.** When the submitted ownership differs from the class of the type (for example 37 of 58 gov_se reports say partner; 20 of 25 Deaf Reach say other), keep the class colour and show "submitted ownership differs" in Data Quality. A reviewed facility-level override wins when supplied. In the "with suggested corrections" view, a gov_se report named Deaf Reach moves to deaf_reach and turns blue. Never recolour silently.

## 7.2 Layers and behaviour

- **Layers:** divisions, districts, service coverage, beneficiary choropleth, facility markers (qualifying coordinates only), marker clustering and an optional density heatmap.

- **Service icons and shapes:** see 7.1 and docs/gis_icon_map.csv. Regional Director offices appear as a green dashed office marker in the admin Offices view and are never counted as a service. Icons describe facility services, not people.

- **District hover:** division, district, reporting facilities, active / new / waiting counts, service availability and coverage %. Clicking a district applies the global district filter.

- **Facility click:** official name, type, location, status, reporting period, unique active / new / waiting, gender breakdown, services and a link to the facility profile. No individual records.

- **Export:** JPG of the complete Sindh extent every time (not the current zoom), with the filtered markers, title, filters, period, legend, source, last-refreshed timestamp and disclaimer; HTML optional (Section 8).

## 7.3 Facility coordinate rules

| **Source**                                       | **Status label**           | **Rule**                                                                                                                                                                                        |
|--------------------------------------------------|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Registry approved coordinates**                | Verified                   | Preferred. Always used when present.                                                                                                                                                            |
| **Submission GIS geopoint (also \_geolocation)** | Reported, not yet verified | Use only if the registry has none, the point lies inside Sindh and inside the polygon of the submitted district, and the latest submissions agree. Otherwise flag "Missing / invalid location". |
| **No usable coordinates**                        | Missing location           | Show the district polygon shading and a labelled facility list. Never place pins at guessed locations or district centroids.                                                                    |

## 7.4 Panels beside the map

| **Panel**           | **Content**                                                                                                                                                                                                                                             |
|---------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Headline**        | Main total beneficiaries (Direct); Total indirect beneficiaries (Estimated, family x 5); Total reach (Estimated).                                                                                                                                       |
| **By service type** | One card or bar per service (all 18; "No reports" where empty): Direct, reports, male / female / other where W was usable, new, waiting.                                                                                                                |
| **Data received**   | Reports received, distinct facilities, districts reporting x of 30, last submission time (Asia/Karachi), source mix (W / section / zero / review), and the latest 10 reports (facility, type, district, period, Direct). No contact or personal fields. |
| **Filters**         | Service type, ownership class, region and district filters sit above the map and apply to markers and panels.                                                                                                                                           |
| **Selection**       | Clicking a marker or a service card filters every other panel.                                                                                                                                                                                          |

All panels follow the global filters and the Active / Cumulative toggle.

# 8. Charting, drill-downs and exports

- **Charts:** Plotly line / area for trends, grouped bars for district and division comparison, donut for gender, horizontal bars for service outputs, district × service heatmap, and conditionally formatted tables. Provide an accessible table alternative for every chart and map.

- **Trends:** use compatible period definitions. Show missing periods as missing, not zero. Show period-over-period change only for comparable facility cohorts, or label the cohort change.

- **Facility detail tabs:** Overview, Beneficiaries, Services, Program-specific Metrics, Reporting History, Data Quality, Map. Tooltips show definitions and units.

- **Pivot builder:** rows division / district / facility / service; columns period, facility type or programme; values from the metric dictionary. Aggregation follows the rule in Appendix A (latest snapshot, sum of periods, or count distinct).

- **Every table can be downloaded as Excel (.xlsx) and as an image (.jpg).** Each table (breakdowns, Summary Reports, Summary Sheet, pivots, data quality lists, facility directory) has a Download Excel and a Download JPG button. The files contain exactly the rows and columns on screen under the active filters, with a title, the active filters, reporting period, Active / Cumulative basis, source and last-refreshed time (Asia/Karachi). The JPG shows the first 60 rows and says so; the Excel file holds all rows. Reference code: src/export/exporters.py.

- **Charts** download as JPG / PNG at 2x or 3x resolution (Plotly / Kaleido). A management PDF (title, date, filter chips, legend, definitions) is also offered. Exports respect the viewer role and never include restricted fields.

- **Map download:** every map export is a JPG of the complete Sindh extent (total bounds of the approved boundary file plus a margin), regardless of the current zoom or pan. It shows the filtered markers (service type, ownership class, region, district), the legend (colour, shape, icon), title, filters, period, source and refreshed time. The image is rendered on the server (GeoPandas / Matplotlib) so it does not depend on the browser view.

# 9. Data ingestion and transformation

- **Live source (primary):** the saved Kobo export setting, an XLSX export of all submissions: https://kf.kobotoolbox.org/api/v2/assets/agqkhZsLaqUQyLK8UwKrsx/export-settings/esqPMKgPTD8ZYEERvWqhw9K/data.xlsx . Read it with HTTP GET and the header Authorization: Token \<token\> unless the export is set to anonymous access in Kobo. The URL and token are configuration (environment variables or Streamlit secrets: KOBO_EXPORT_URL, KOBO_API_TOKEN), never hard-coded, so the source can change without code changes and the app can move to another server.

- **Export settings must not change silently:** the saved setting fixes the column names (XML names, no group prefixes, select_multiple expanded as field/choice 0/1 columns, all versions off). The loader checks required columns on every load and stops with a clear schema error if the export settings were changed.

- **Load behaviour:** the export is generated on request and can take several seconds. Use a timeout (default 120 s), up to 3 retries with back-off, a cache (default 15 minutes) and a visible "Last refreshed" stamp. If the call fails, keep serving the last good copy, marked "stale", and fall back to a local XLSX in data/ only for tests. Never log the token or the full URL with credentials.

- **Strip restricted columns at load:** the export contains contact, signature, picture and story fields. Remove them from the general dataframe immediately and keep them only for admin and manager views.

- **Optional alternative:** the v2 JSON data endpoint (/api/v2/assets/{uid}/data/?format=json) with pagination, if the XLSX export becomes too slow. Same canonical mapping.

- **Source adapter:** map exported columns to canonical names using Appendix A (the current export has no group prefixes; tolerate them, for example sec_w/w_total, if the export settings change), and keep raw values for audit. Read cells as text first and convert numbers explicitly, so blank stays distinct from 0.

- **Kobo system fields to keep:** \_id, \_uuid, \_submission_time, \_validation_status, \_geolocation, start, end, and the form version. Use start / end for a completion-time quality check.

- **Geography:** join district to division using the 30-district list. Flag mismatches. Analytics use the validated mapping. Keep the original for diagnostics.

- **Facility registry** (governed, separate): stable facility_id, normalised name, facility_type, district, division, approved location, expected reporting status, optional services, and reviewed alias mappings.

- **Deduplication key:** facility_id + rp_end (rp_start is the facility inception date, not a period start). The latest approved submission wins when a facility registry gives a reliable facility_id. Without one, do NOT deduplicate by name: in the 107-row export, 12 groups (32 reports) share one centre name, district and month (several Deaf Reach satellite schools and digital classes), and removing them would lower Direct from 7,728 to 7,112. Count every submission, flag each group for review, and let an admin mark reviewed duplicates. Keep all revisions in an audit view. Recommended form change: add a centre name or code (decision 24).

- **Multi-select fields:** normalise space-separated codes or expanded 0/1 columns into coverage flags. Treat blank (not applicable) differently from 0.

- **Derived tables:** fact_facility_period, dim_facility, dim_district, dim_division, dim_service, fact_service_output, submission_quality. Use pandas and NumPy. Avoid a heavy database at first.

- **Testability:** adapters run on local XLSX / CSV / JSON fixtures. Production credentials live in secrets, not in an editable API-entry form in the app.

# 10. Programme-specific drill-downs

| **Programme**           | **Required drill-down**                                                                                                                                                                                                | **Key fields**                                                 |
|-------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------|
| **NOWPDP**              | P1 Shanakht: applications, CNICs issued, pending. P2 Taleem: enrolment and packages. P3 Hunar: active, completed, dropout, courses. P4 Rozgar: jobs and self-employment. P5 Suvaari: recipients and device quantities. | p_cum; p1\_\*; p2\_\*; p3\_\*; p4\_\*; p5\_\*; nowpdp_programs |
| **C-ARTS**              | V1 education, V2 therapy sessions, V3 vocational, V4 adult / ADHD livelihoods, V5 parent training. Parent trainees are excluded from the disability beneficiary total.                                                 | carts_services; v1\_\* to v5\_\*; q\_\*                        |
| **SIPMR**               | OPD, unique therapy patients versus sessions, prosthetics and orthotics made / fitted / repaired, waiting.                                                                                                             | l\_\*; u\_\*                                                   |
| **Deaf Reach**          | Cumulative and active students, jobs, transport riders, km/day, teacher training, PSL vocabulary.                                                                                                                      | t\_\*                                                          |
| **Inclusive Education** | Integrated and enrolled students, schools, graduates, master-teacher training, monitoring visits.                                                                                                                      | n\_\*                                                          |
| **Other facilities**    | RCMHC / RCPH (C), government special education (C, M), PCRDP (G1), hostel (I), academy (H), vocational (K), assistive device partners (R).                                                                             | c\_\*; m\_\*; g1\_\*; i\_\*; h\_\*; k\_\*; r\_\*               |

# 11. Privacy, security, accessibility and quality

## 11.1 Privacy and security

- **Aggregate data only.** No names, CNICs, personal phone numbers, individual disability history or beneficiary-level markers.

- **Restricted fields:** contact_name, contact_info, signature, pictures and story files are visible only to admin and manager roles. Pictures appear only where a data-protection approval exists.

- **Roles:** admin, manager, regional coordinator, viewer. Enforce region and facility permissions on the server (data filtered before it reaches the page). Hiding widgets is not security.

- **Hosting:** confirm that the Streamlit Community Cloud, or an alternative, meets DEPD data-residency and access policy. Use real sign-in (for example OIDC) rather than a shared password. See Section 14.

## 11.2 Accessibility

- WCAG 2.1 AA goals, keyboard navigation, descriptive chart labels, readable contrast, icons plus text, no colour-only encoding, and table alternatives for every map and chart.

## 11.3 Diagnostics (Data Quality page)

| **Check**                             | **Rule**                                                                                                                                                             |
|---------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Missing or invalid geography**      | Missing district; district not in the 30-district list; division does not match district.                                                                            |
| **Unrecognised facility**             | No registry match or alias for facility_name.                                                                                                                        |
| **Duplicate periods**                 | Same facility with the same rp_end, or two reports in the same month or quarter.                                                                                     |
| **Stale or late reports**             | No submission for the expected period; submission_date after the agreed deadline.                                                                                    |
| **Impossible values**                 | Negative numbers; rp_end before rp_start; submission_date before rp_end; rp_end in the future.                                                                       |
| **Active above capacity**             | w_total above capacity, or v1_active above v1_cap.                                                                                                                   |
| **Active versus cumulative**          | Active above the cumulative figure in the same programme (c_active \> c_cumulative, n_enrolled \> n_integrated, p2_active \> p2_integrated, and the V1 to V5 pairs). |
| **W zero or blank with section data** | w_total is 0 or blank while the section figure (c_active, n_enrolled, v-section active) is above 0. Direct resolved from the section (5.3).                          |
| **W copied from cumulative**          | w_total equals c_cumulative while c_active differs. Direct resolved from the section.                                                                                |
| **W versus section mismatch**         | Difference above 20%. W kept; flagged "review" with both numbers.                                                                                                    |
| **All-zero report**                   | Direct = 0 from W and the section. Flag; if devices were given in the same report, mark "probably missing data".                                                     |
| **Misclassified facility type**       | Name contains "deaf reach" but type is gov_se (12 in the sample). Show suggested type; apply only through a reviewed override.                                       |
| **Near-duplicate facility names**     | Same district, type and rp_end with similar normalised names (case, punctuation, "&" versus "and", typos).                                                           |
| **New above active**                  | New beneficiaries above the active figure (for example new 500 with active 152; new 90 with active 1). Possible but unusual: flag for review.                        |
| **Division mismatch**                 | Submitted division differs from the division of the district. Totals use the district mapping.                                                                       |
| **Contact field misuse**              | contact_name, contact_info or officer_designation holds only digits or "0". Restricted fields; flag only.                                                            |
| **Period meaning**                    | rp_start equal to rp_end, or rp_start later than the facility's first report. rp_start is treated as the inception date.                                             |
| **Active headcount mismatch**         | w_total differs from the section-level active figure (c_active, n_enrolled, v-section active) for the same facility.                                                 |
| **Gender total**                      | w_total is not the sum of the four gender fields (calculation tampered with or form edited).                                                                         |
| **Device double-count risk**          | nowpdp submission with P5 and R quantities both above zero.                                                                                                          |
| **C-ARTS parents**                    | V5 parent counts included in a disability beneficiary total.                                                                                                         |
| **Location**                          | No coordinates; GIS point outside Sindh or outside the submitted district.                                                                                           |
| **Verification**                      | Form verification_status = not_verified, or Kobo \_validation_status not Approved.                                                                                   |
| **Completion time**                   | Very short start-to-end duration (for example under 60 seconds) on a long submission.                                                                                |
| **API / sync**                        | Failed or partial refresh, schema change, unknown new field.                                                                                                         |

**No fictitious KPI figures.** Show "No data", "Not applicable", "Not collected", "Not yet verified" and "Missing location" as distinct states.

# 12. Development stack and implementation plan

Python 3.10+; Streamlit, pandas, NumPy, Plotly, GeoPandas / Shapely, Folium or PyDeck (streamlit-folium where needed), requests / httpx, openpyxl, XlsxWriter, Matplotlib, Pillow, Kaleido and reportlab. Simple modular architecture with caching. Suggested cache time 15 minutes, with a manual refresh for admins only.

| **Phase**                   | **Acceptance requirement**                                                                                                                                                                                                                                                                                         |
|-----------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **1. Data contract**        | Read the XLSForm. Produce a mapping CSV / JSON for all fields (starting from Appendix A). Verify a Kobo API export against the schema, including group prefixes and select_multiple format.                                                                                                                        |
| **2. Core data layer**      | Facility registry, 30 districts / 6 divisions, latest-period selection, duplicate handling, canonical KPIs (Section 5), unit tests. Test: coalesce rules return the right source for all 18 services, and the Direct / family / total rules reproduce tests/expected_sample_107.json and tests/expected_kpis.json. |
| **3. Executive dashboard**  | Responsive cards, charts, synchronised division / district / facility filters, period selector. Test: every number on screen reconciles with the filtered dataframe.                                                                                                                                               |
| **4. GIS**                  | Correct polygons and colours, category icons, coordinate rules (7.3), hover and click drill-down, export.                                                                                                                                                                                                          |
| **5. Programme dashboards** | NOWPDP, C-ARTS, SIPMR, Deaf Reach, Inclusive Education and other facility metrics; service pivots with correct aggregation.                                                                                                                                                                                        |
| **6. Security and QA**      | Roles, restricted fields, Data Quality page (11.3), exports, mobile tests, accessibility check, deployment instructions.                                                                                                                                                                                           |

## 12.1 Build, run and deployment (portable)

- **Build:** Antigravity builds the code from this specification and the prompts. The project folder is the source of truth for rules and tests.

- **Run:** Python 3.11 and Streamlit. The app reads only configuration from environment variables or .streamlit/secrets.toml, so the same code runs on a laptop, an office server or a cloud host.

- **Portable deployment:** the folder includes a Dockerfile, docker-compose.yml, .env.example and docs/deployment.md. Moving to another server means copying the folder, setting the environment variables (Kobo URL and token, sign-in settings) and running docker compose up -d.

- **Sign-in and roles:** viewer, regional coordinator, manager and admin, enforced on the server. Put the app behind HTTPS (reverse proxy such as Nginx or Caddy) and the department's sign-in method (decision 8).

- **Operations:** health check, structured logs without secrets, cache refresh by admin only, and a nightly snapshot of the last good dataset so the dashboard still opens if Kobo is unreachable.

# 13. Developer prompt

The full, paste-ready prompt is prompts/dashboard_developer_prompt_v2.md in the project folder. Summary:

Act as a senior Python / Streamlit engineer, GIS analyst and public-sector data architect. Implement the DEPD Executive Analytics & GIS Dashboard described in this document (Version 1.3).

- Use the latest Kobo XLSForm as the exact schema and the Version 7 Word form for business definitions. Do not invent data, fields, coordinates, beneficiary identities or boundaries. Compare the form with Appendix A and report any difference before coding.

- **Do not trust w_total alone.** Resolve Direct beneficiaries with the rules in 5.3 (W first, then the section figure when W is blank, zero or copied from cumulative), implemented as tested library code that matches tests/reference_resolution.py.

- Show the Reach summary: Direct, Indirect (family) = Direct x 5, and Total reach = Direct + Indirect, on an Active / Cumulative toggle. F = 5 is an admin setting. The estimate is always labelled "Estimated". Reported indirect reach is a separate card and is never added.

- Read live data from the Kobo export-settings URL (Section 9) using KOBO_EXPORT_URL and KOBO_API_TOKEN from configuration. Treat regional_dir as office information only (not a service). Colour map markers by the DEPD ownership class of the service type (green, blue, purple), use a different shape for health, education and training, and add service icons (Section 7.1).

- Use rp_end for periods; treat rp_start as the inception date. Never auto-correct stored values: use reviewed override tables.

- Implement the canonical KPI rules (Section 5), device mapping (5.2), facility routing (Section 6), coordinate rules (7.3) and diagnostics (11.3) exactly as written.

- Deliver modular production-quality code, requirements.txt, .streamlit/config.toml, an example secrets template, unit tests (52 cases in tests/test_cases.md), a setup README and sample data clearly labelled synthetic.

- If the Kobo token, facility registry or boundary GeoJSON is missing, use a clearly marked placeholder and explain the missing dependency. Never invent it.

# 14. Decisions needed before production

| **\#** | **Decision**                                                                                                                                                                                                                                         | **Why it matters**                                                            | **Default if no answer**                                                    |
|--------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| 1      | Kobo server, API token permissions, deployed asset UID, and whether fields carry group prefixes.                                                                                                                                                     | Needed to connect.                                                            | Placeholder; fixture data.                                                  |
| 2      | Approved district / division boundary dataset and facility registry with verified coordinates.                                                                                                                                                       | Map accuracy and coverage %.                                                  | District-only map; no pins.                                                 |
| 3      | Reporting cadence (monthly, quarterly, other), approval workflow and the expected-facility denominator.                                                                                                                                              | Trends and coverage %.                                                        | Derive from rp_end; no coverage %.                                          |
| 4      | Canonical version name (Word header says "Version 5").                                                                                                                                                                                               | Document consistency.                                                         | Use "Version 7".                                                            |
| 5      | Is a true age distribution required? That needs numeric age counts in the Kobo form.                                                                                                                                                                 | The form has age-group checkboxes only.                                       | Coverage view only.                                                         |
| 6      | Confirm the device source rule in 5.2, or tell NOWPDP to leave Section R empty.                                                                                                                                                                      | Avoids double counting.                                                       | P5 for nowpdp, R otherwise.                                                 |
| 7      | Is the sum of facility-reported headcounts acceptable, or is an external deduplication source needed?                                                                                                                                                | Credibility of totals.                                                        | Label as facility-reported.                                                 |
| 8      | Hosting and sign-in method that meets DEPD data policy.                                                                                                                                                                                              | Security and residency.                                                       | Private deployment with sign-in.                                            |
| 9      | English only, or English and Urdu labels in the dashboard.                                                                                                                                                                                           | Usability for staff.                                                          | English only.                                                               |
| 10     | Total reach: Direct + Direct x 5, or Direct x 5 only?                                                                                                                                                                                                | Changes the headline number.                                                  | Direct + Direct x 5.                                                        |
| 11     | Family factor F.                                                                                                                                                                                                                                     | Changes the estimate.                                                         | 5, admin setting.                                                           |
| 12     | Should a facility's own reported indirect reach replace the x5 estimate for that facility?                                                                                                                                                           | Possible overlap of the same people.                                          | No, shown separately.                                                       |
| 13     | When W and the section figure differ by more than 20%, which is right?                                                                                                                                                                               | Changes Direct for 8 of 107 sample reports.                                   | Keep W, flag for review.                                                    |
| 14     | Should dis_cer, SPDPA and legal-support facilities fill Section W?                                                                                                                                                                                   | They only have cumulative figures; W is not meaningful for them.              | Yes for now; Cumulative basis.                                              |
| 15     | Is rp_start the facility inception date? Should the form get a separate period-start question?                                                                                                                                                       | Needed to detect overlapping reports.                                         | Inception date; period from rp_end.                                         |
| 16     | PCRDP: still shows Section C but no G1. Is SPDPA replacing PCRDP?                                                                                                                                                                                    | Wrong questions for PCRDP users.                                              | Treat as built; flag.                                                       |
| 17     | Rename auto-generated field names (group_dp8mz64, Cumulative_Disabilit\_..., legal_support\_\_beneficiaries) before collecting more data?                                                                                                            | Readable exports; renaming later breaks columns.                              | Use as exported.                                                            |
| 18     | Service breakdown default: "as filed" or "with suggested corrections"?                                                                                                                                                                               | Deaf Reach reports filed as gov_se change service (20 in the 107-row export). | As filed, with a banner and a toggle.                                       |
| 19     | Ownership class by service type (government: RCMHC, RCPH, government special education, C-ARTS, VTC, SPDPA, disability certificate, inclusive, Regional Director; partner: assistive devices, GIA, Deaf Reach) and confirmation of the purple types. | Submitted ownership is unreliable.                                            | DEPD rule in data/ownership_by_type.csv; submitted value is a check.        |
| 20     | Kobo export access: token owner, anonymous access or not, and who may change the export setting.                                                                                                                                                     | A changed export setting breaks columns.                                      | Token in secrets; schema check on every load.                               |
| 21     | Hosting target and sign-in for the live deployment (Docker on a DEPD or cloud server).                                                                                                                                                               | Security and portability.                                                     | Docker, private network, sign-in.                                           |
| 22     | Regional Director is office information only.                                                                                                                                                                                                        | Avoids counting an office as a service.                                       | Excluded from services and totals.                                          |
| 23     | Do Assistive Devices (assistive_ip) recipients count as Direct?                                                                                                                                                                                      | Changes Direct by 208 in the 107-row export.                                  | Yes, flagged as a period count.                                             |
| 24     | Same centre name in the same district and month: duplicate or different centres? Add a facility ID or centre code to the form?                                                                                                                       | 32 reports in 12 groups; Direct 7,728 vs 7,112 if all were duplicates.        | Count all; flag groups; admin marks reviewed duplicates.                    |
| 25     | SPDPA row filed by an NGO (Ida Rieu): wrong facility type?                                                                                                                                                                                           | Direct 1,054 sits under a registration type.                                  | Keep value, flag "type may be wrong".                                       |
| 26     | The form has grown: about 660 export columns are not in the field dictionary (including a rewritten assistive-device section R1 to R5, still empty). Share the latest XLSForm.                                                                       | Appendix A may miss new fields.                                               | Loader ignores unknown columns with a warning; Phase 1 reports differences. |

# Appendix A. Metric dictionary (generated from the XLSForm of 4 Nov 2026)

The live form has since grown (about 660 export columns are not listed here, including the rewritten assistive-device section R1 to R5, still empty in all reports). Phase 1 must regenerate this appendix from the newest XLSForm and report differences. Unknown columns never break the load.

Every number field in the form (143, plus the calculated w_total). Unit "people (indirect reach)" fields are never added to Direct. Some Total\_\* legal-support fields have no period hint in the form: they are assumed cumulative (CUM) except Total_Ongoing_Cases (SNAP); confirm and add hints. **Rule codes:** CUM = latest cumulative snapshot per facility; SNAP = latest snapshot at reporting end date; FLOW = sum over distinct reporting periods. Section letters match the form. Regenerate this table if the form changes.

| **Field**                                                                    | **Indicator**                                                                       | **Unit**                | **Rule** |
|------------------------------------------------------------------------------|-------------------------------------------------------------------------------------|-------------------------|----------|
| **Section B — Operational profile**                                          |                                                                                     |                         |          |
| **capacity**                                                                 | Approved beneficiary capacity (if applicable)                                       | seats / places          | FLOW     |
| **Section C — RCMHC, RCPH, Govt SE, GIA**                                    |                                                                                     |                         |          |
| **c_cumulative**                                                             | Total unique beneficiaries served since establishment                               | people                  | CUM      |
| **Total_indirect_reach_since_inception**                                     | Total indirect reach since inception                                                | people (indirect reach) | CUM      |
| **c_active**                                                                 | Active beneficiaries currently enrolled / receiving treatment                       | people                  | SNAP     |
| **c_waiting**                                                                | Unique beneficiaries on active waiting list                                         | people                  | SNAP     |
| **c_new**                                                                    | New beneficiaries registered                                                        | people                  | FLOW     |
| **c_completed**                                                              | Beneficiaries completing rehabilitation / education                                 | people                  | FLOW     |
| **c_rcmhc_multi**                                                            | RCMHC: Children receiving multidisciplinary rehabilitation                          | people                  | FLOW     |
| **c_rcph_mobility**                                                          | RCPH: Patients receiving mobility training                                          | people                  | FLOW     |
| **c_rcph_fitted**                                                            | RCPH: Unique beneficiaries fitted with prosthetic / orthotic devices                | people                  | FLOW     |
| **Section G1 — SPDPA registration & complaints**                             |                                                                                     |                         |          |
| **g1_received**                                                              | Registrations received                                                              | registrations           | FLOW     |
| **g1_approved**                                                              | Registrations approved                                                              | registrations           | FLOW     |
| **g1_rejected**                                                              | Registrations rejected                                                              | registrations           | FLOW     |
| **g1_pending**                                                               | Registrations still pending                                                         | registrations           | SNAP     |
| **g1_issued**                                                                | Certificates / ID cards issued                                                      | certificates / cards    | FLOW     |
| **g1_complaints**                                                            | Complaints received                                                                 | complaints              | FLOW     |
| **g1_resolved**                                                              | Complaints resolved                                                                 | complaints              | FLOW     |
| **Section G1 — Disability Certificate group**                                |                                                                                     |                         |          |
| **Cumulative_Disabilit_sued_Since_Inception**                                | Cumulative Disability Certificates Issued Since Inception                           | certificates            | CUM      |
| **Cumulative_Disabilit_Female_Beneficiaries**                                | Cumulative Disability Certificates Issued to Female Beneficiaries                   | certificates            | CUM      |
| **Cumulative_Disabilit_o_Male_Beneficiaries**                                | Cumulative Disability Certificates Issued to Male Beneficiaries                     | certificates            | CUM      |
| **Cumulative_Disabilit_gender_Beneficiaries**                                | Cumulative Disability Certificates Issued to Khwajasira / Transgender Beneficiaries | certificates            | CUM      |
| **Number_of_certificat_o_children_under_18**                                 | Number of certificates issued to children (under 18)?                               | certificates            | CUM      |
| **Number_of_certificat_issued_to_adults_18**                                 | Number of certificates issued to adults (18+)?                                      | certificates            | CUM      |
| **Section H — Training Academy**                                             |                                                                                     |                         |          |
| **h_completed**                                                              | Trainees completed / certified                                                      | people                  | FLOW     |
| **h_dropped**                                                                | Trainees dropped out                                                                | people                  | FLOW     |
| **h_trainers**                                                               | Trainers present                                                                    | people                  | SNAP     |
| **Section K — Vocational**                                                   |                                                                                     |                         |          |
| **k_completed**                                                              | Trainees completed                                                                  | people                  | FLOW     |
| **k_dropped**                                                                | Trainees dropped out                                                                | people                  | FLOW     |
| **k_placed**                                                                 | Trainees placed in jobs / self-employment                                           | people                  | FLOW     |
| **Section L — Medical / Physical Rehabilitation**                            |                                                                                     |                         |          |
| **l_opd**                                                                    | OPD visits                                                                          | visits                  | FLOW     |
| **l_assess**                                                                 | Assessments done                                                                    | assessments             | FLOW     |
| **l_referrals**                                                              | Referrals made                                                                      | referrals               | FLOW     |
| **Section N — Inclusive Education**                                          |                                                                                     |                         |          |
| **n_integrated**                                                             | Beneficiaries integrated into mainstream schools                                    | people                  | CUM      |
| **n_enrolled**                                                               | Beneficiaries enrolled in inclusive classrooms                                      | people                  | SNAP     |
| **n_waiting**                                                                | Beneficiaries on inclusive education waiting list                                   | people                  | SNAP     |
| **n_schools**                                                                | Mainstream inclusive schools registered / identified                                | schools                 | SNAP     |
| **n_graduated**                                                              | Students with disabilities graduated / passed out                                   | people                  | FLOW     |
| **n_tot**                                                                    | Mainstream master teachers trained in inclusive education (ToT)                     | people                  | FLOW     |
| **n_new**                                                                    | New students with disabilities integrated into mainstream schools                   | people                  | FLOW     |
| **n_visits**                                                                 | Inclusive education monitoring visits conducted                                     | visits                  | FLOW     |
| **Section Q — Partner Report (C-ARTS)**                                      |                                                                                     |                         |          |
| **q_male**                                                                   | People reached — Male                                                               | people                  | FLOW     |
| **q_female**                                                                 | People reached — Female                                                             | people                  | FLOW     |
| **q_trans**                                                                  | People reached — Transgender                                                        | people                  | FLOW     |
| **q_other**                                                                  | People reached — Other / not recorded                                               | people                  | FLOW     |
| **Section R — Assistive Devices**                                            |                                                                                     |                         |          |
| **r_male**                                                                   | People who received devices — Male                                                  | people                  | FLOW     |
| **r_female**                                                                 | People who received devices — Female                                                | people                  | FLOW     |
| **r_trans**                                                                  | People who received devices — Transgender                                           | people                  | FLOW     |
| **r_other**                                                                  | People who received devices — Other / not recorded                                  | people                  | FLOW     |
| **r_wheelchair**                                                             | Wheelchair (manual / electric)                                                      | devices                 | FLOW     |
| **r_crutches**                                                               | Crutches / walking sticks                                                           | devices                 | FLOW     |
| **r_walker**                                                                 | Walker / rollator                                                                   | devices                 | FLOW     |
| **r_limb**                                                                   | Artificial limb (prosthesis)                                                        | devices                 | FLOW     |
| **r_orthosis**                                                               | Orthosis / calipers / braces                                                        | devices                 | FLOW     |
| **r_hearing**                                                                | Hearing aid                                                                         | devices                 | FLOW     |
| **r_spectacles**                                                             | Spectacles / low-vision aid                                                         | devices                 | FLOW     |
| **r_dev_other**                                                              | Other devices                                                                       | devices                 | FLOW     |
| **Section T — Deaf Reach**                                                   |                                                                                     |                         |          |
| **t_cum**                                                                    | Beneficiary students enrolled since program inception                               | people                  | CUM      |
| **Beneficiary_students_inception_In_Direct**                                 | Beneficiary students enrolled since program inception In-Direct                     | people (indirect reach) | CUM      |
| **t_placed**                                                                 | Graduates placed in permanent jobs                                                  | people                  | CUM      |
| **t_await_job**                                                              | Graduates currently awaiting employment placement                                   | people                  | SNAP     |
| **t_transport**                                                              | Active students using pick-and-drop transport                                       | people                  | SNAP     |
| **t_km**                                                                     | Total daily distance covered by all transport vehicles (KM/day)                     | km per day              | SNAP     |
| **t_teachers**                                                               | Educators trained as specialized deaf teachers                                      | people                  | FLOW     |
| **t_psl**                                                                    | Digital vocabulary words documented in PSL Dictionary                               | words                   | CUM      |
| **Section U — SIPMR**                                                        |                                                                                     |                         |          |
| **u_cum**                                                                    | Unique patients rehabilitated since establishment                                   | people                  | CUM      |
| **u_discharged**                                                             | Patients safely discharged after completing rehabilitation                          | people                  | FLOW     |
| **u_physio_pts**                                                             | Unique physiotherapy patients served                                                | people                  | FLOW     |
| **u_physio_ses**                                                             | Physiotherapy sessions conducted                                                    | sessions                | FLOW     |
| **u_ot_pts**                                                                 | Unique occupational therapy patients served                                         | people                  | FLOW     |
| **u_ot_ses**                                                                 | Occupational therapy sessions conducted                                             | sessions                | FLOW     |
| **u_speech_pts**                                                             | Unique speech therapy patients served                                               | people                  | FLOW     |
| **u_speech_ses**                                                             | Speech therapy sessions conducted                                                   | sessions                | FLOW     |
| **u_prosth_made**                                                            | Custom prosthetic devices manufactured                                              | devices                 | FLOW     |
| **u_orth_made**                                                              | Custom orthotic devices manufactured                                                | devices                 | FLOW     |
| **u_fitted**                                                                 | Unique beneficiaries fitted with prosthetic / orthotic devices                      | people                  | FLOW     |
| **u_repaired**                                                               | Prosthetic / orthotic devices repaired or adjusted                                  | devices                 | FLOW     |
| **u_await_dev**                                                              | Patients awaiting prosthetic / orthotic devices                                     | people                  | SNAP     |
| **Section V1 — C-ARTS Special Education**                                    |                                                                                     |                         |          |
| **v1_cum**                                                                   | Student beneficiaries enrolled since establishment                                  | people                  | CUM      |
| **v1_active**                                                                | Student beneficiaries currently enrolled                                            | people                  | SNAP     |
| **v1_wait**                                                                  | Child beneficiaries on active education waiting list                                | people                  | SNAP     |
| **v1_cap**                                                                   | Approved enrolment capacity (classroom seats)                                       | seats / places          | SNAP     |
| **v1_exit**                                                                  | Beneficiaries completing or exiting the program                                     | people                  | FLOW     |
| **Section V2 — C-ARTS Therapy**                                              |                                                                                     |                         |          |
| **v2_cum**                                                                   | Therapy beneficiaries served since establishment                                    | people                  | CUM      |
| **v2_active**                                                                | Therapy beneficiaries actively receiving treatment                                  | people                  | SNAP     |
| **v2_wait**                                                                  | Therapy beneficiaries on active waiting list                                        | people                  | SNAP     |
| **v2_sessions**                                                              | Therapy sessions conducted                                                          | sessions                | FLOW     |
| **Section V3 — C-ARTS Vocational**                                           |                                                                                     |                         |          |
| **v3_cum**                                                                   | Vocational beneficiaries trained since establishment                                | people                  | CUM      |
| **v3_active**                                                                | Vocational beneficiaries currently enrolled                                         | people                  | SNAP     |
| **v3_wait**                                                                  | Vocational beneficiaries on active waiting list                                     | people                  | SNAP     |
| **v3_completed**                                                             | Trainees successfully completing training                                           | people                  | FLOW     |
| **v3_placed**                                                                | Trainees placed in jobs or self-employment                                          | people                  | FLOW     |
| **Section V4 — C-ARTS Adult & ADHD**                                         |                                                                                     |                         |          |
| **v4_cum**                                                                   | Adult beneficiaries engaged since establishment                                     | people                  | CUM      |
| **v4_active**                                                                | Adult beneficiaries currently participating                                         | people                  | SNAP     |
| **v4_wait**                                                                  | Adult beneficiaries on active waiting list                                          | people                  | SNAP     |
| **v4_livelihood**                                                            | Adults in livelihood / employment tracks (café, organic farming, etc.)              | people                  | SNAP     |
| **Section V5 — C-ARTS Parent Training**                                      |                                                                                     |                         |          |
| **v5_cum**                                                                   | Parent beneficiaries trained since establishment                                    | people                  | CUM      |
| **v5_active**                                                                | Parents currently enrolled in active training cycles                                | people                  | SNAP     |
| **v5_wait**                                                                  | Parents on active waiting list for upcoming cohorts                                 | people                  | SNAP     |
| **v5_sessions**                                                              | Parent training sessions held                                                       | sessions                | FLOW     |
| **Section P0 — NOWPDP summary**                                              |                                                                                     |                         |          |
| **p_cum**                                                                    | Total unique beneficiaries served across all programs                               | people                  | CUM      |
| **Section P1 — Shanakht**                                                    |                                                                                     |                         |          |
| **p1_cnic**                                                                  | Unique individuals facilitated with Special CNICs                                   | people                  | CUM      |
| **p1_apps**                                                                  | New legal registration applications initiated                                       | cases                   | FLOW     |
| **p1_issued**                                                                | Special CNIC cases processed and issued                                             | cases                   | FLOW     |
| **p1_pending**                                                               | Pending verification cases with NADRA / Social Welfare                              | cases                   | SNAP     |
| **p1_guidance**                                                              | Beneficiaries receiving legal / procedural guidance only                            | people                  | FLOW     |
| **Section P2 — Taleem**                                                      |                                                                                     |                         |          |
| **p2_integrated**                                                            | Children with disabilities integrated into classrooms                               | people                  | CUM      |
| **p2_active**                                                                | Active students currently enrolled in education programs                            | people                  | SNAP     |
| **p2_waiting**                                                               | Out-of-school children with disabilities on active education waiting list           | people                  | SNAP     |
| **p2_packages**                                                              | School Essential Packages (bags, uniforms, books) distributed                       | items                   | FLOW     |
| **p2_graduated**                                                             | Students with disabilities passing annual exams / graduating                        | people                  | FLOW     |
| **Section P3 — Hunar**                                                       |                                                                                     |                         |          |
| **p3_cert**                                                                  | Unique trainees certified                                                           | people                  | CUM      |
| **p3_active**                                                                | Active trainees currently attending vocational courses                              | people                  | SNAP     |
| **p3_waiting**                                                               | Eligible applicants on active waiting list for training                             | people                  | SNAP     |
| **p3_completed**                                                             | Trainees completing trade courses                                                   | people                  | FLOW     |
| **p3_dropped**                                                               | Trainees dropping out / discontinuing training                                      | people                  | FLOW     |
| **Section P4 — Rozgar**                                                      |                                                                                     |                         |          |
| **p4_cum**                                                                   | Graduates placed in permanent corporate / banking jobs                              | people (placements)     | CUM      |
| **p4_new**                                                                   | Corporate job placements secured                                                    | people (placements)     | FLOW     |
| **p4_await**                                                                 | Trained job-seekers currently awaiting employment placement                         | people                  | SNAP     |
| **p4_selfemp**                                                               | Beneficiaries establishing small enterprises / self-employment                      | people                  | FLOW     |
| **p4_audits**                                                                | Corporate accessibility audits and sensitization sessions conducted                 | sessions                | FLOW     |
| **Section P5 — Suvaari**                                                     |                                                                                     |                         |          |
| **p5_cum**                                                                   | Unique individuals provided assistive devices                                       | people                  | CUM      |
| **p5_fitted**                                                                | Unique beneficiaries fitted with customized mobility devices                        | people                  | FLOW     |
| **p5_await**                                                                 | People awaiting device measurement / fabrication                                    | people                  | SNAP     |
| **p5_wheelchair**                                                            | Manual wheelchairs distributed                                                      | devices                 | FLOW     |
| **p5_tricycle**                                                              | Customized motorized tri-wheelers distributed                                       | devices                 | FLOW     |
| **p5_crutches**                                                              | Crutches / walking sticks / walkers distributed                                     | devices                 | FLOW     |
| **p5_hearing**                                                               | Hearing aids distributed                                                            | devices                 | FLOW     |
| **p5_cane**                                                                  | White canes / low-vision aids distributed                                           | devices                 | FLOW     |
| **p5_other**                                                                 | Other customized devices distributed                                                | devices                 | FLOW     |
| **Section G2 — Legal support (Access to Justice)**                           |                                                                                     |                         |          |
| **Total_Direct_Benefic_since_establishment**                                 | Total Direct Beneficiaries Served unique counts since establishment                 | people                  | CUM      |
| **Total_Indirect_Reach_ablishment_Indirect**                                 | Total Indirect Reach (Beneficiaries) unique counts since establishment (Indirect)   | people (indirect reach) | CUM      |
| **Total_Ongoing_Cases**                                                      | Total Ongoing Cases                                                                 | cases                   | SNAP     |
| **Total_Closed_Resolved_Cases**                                              | Total Closed / Resolved Cases                                                       | cases                   | CUM      |
| **Total_Court_Representations_Provided**                                     | Total Court Representations Provided                                                | representations         | CUM      |
| **Total_Legal_Advice_Consultations**                                         | Total Legal Advice/Consultations                                                    | consultations           | CUM      |
| **Total_Mobile_Clinic_Participants**                                         | Total Mobile Clinic Participants                                                    | people                  | CUM      |
| **Section W — Global unique beneficiary summary (headline source; see 5.3)** |                                                                                     |                         |          |
| **w_male**                                                                   | Male                                                                                | people                  | SNAP     |
| **w_female**                                                                 | Female                                                                              | people                  | SNAP     |
| **w_trans**                                                                  | Transgender                                                                         | people                  | SNAP     |
| **w_other**                                                                  | Other / Not recorded                                                                | people                  | SNAP     |
| **w_total**                                                                  |                                                                                     | people                  | SNAP     |
| **w_new**                                                                    | Unique new beneficiaries registered                                                 | people                  | FLOW     |
| **w_waiting**                                                                | Unique people on active waiting list                                                | people                  | SNAP     |

Note: gender fields in Q (q_male to q_other) and R (r_male to r_other) count people reached or given devices in the period (FLOW). They are not part of the Section W headline headcount.

# Appendix B. Changes in Version 1.3 (from 1.2)

| **Area**                      | **Change**                                                                                                                                                                                                                                                                                                                                                                    |
|-------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Live data**                 | Kobo export-settings XLSX URL as the primary source (Section 9), token and URL from configuration, schema check, cache, stale-copy fallback, restricted columns stripped at load.                                                                                                                                                                                             |
| **Regional Director**         | regional_dir is office information only: excluded from services, totals and counts; 18 services remain. Admin Offices view and green dashed office marker.                                                                                                                                                                                                                    |
| **Summary Reports**           | New Section 5.7 and page 8: who has updated data by division, district and service type, with beneficiaries, matrix and pending list.                                                                                                                                                                                                                                         |
| **Map**                       | Disability certificate is government. Marker colour by ownership class fixed by service type (green government, blue partner organisation, purple other, grey unknown); marker shape by category (circle health, rounded square education, hexagon training, and others); icons; neutral division polygons; submitted ownership kept as a check; panels beside the map (7.4). |
| **Evidence**                  | 107-row export: Direct 7,728; Indirect (x5) 38,640; Total 46,368; plain sum of w_total 8,267. assistive_ip counts device recipients. One implausible cumulative value (3.37e215).                                                                                                                                                                                             |
| **New fields**                | Provincial, Office_Address_Details, and inclusive-education reported indirect categories (parents / family, peer students, community, school staff).                                                                                                                                                                                                                          |
| **Deployment**                | Section 12.1: portable Docker deployment, health check, nightly snapshot.                                                                                                                                                                                                                                                                                                     |
| **Summary Sheet and exports** | Summary Sheet (service type, region, district, organisation name, beneficiaries); Excel and JPG download for every table; map JPG always of the full Sindh extent; service type, ownership class, region and district filters on every tab including the map; disability certificate moved to government.                                                                     |
| **Decisions**                 | Added 19 to 26.                                                                                                                                                                                                                                                                                                                                                               |

# Appendix C. Changes in Version 1.2 (from 1.1)

| **Area**                  | **Change**                                                                                                                                                                                                                                                                                  |
|---------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Beneficiary counting**  | New Sections 5.3 to 5.5: Direct is resolved per submission (W first, then the section figure when W is blank, zero or copied from cumulative); Indirect (family) estimate = Direct x 5; Total reach = Direct + Indirect; reported indirect reach kept separate. Active / Cumulative toggle. |
| **Evidence**              | Source audit now includes a 43-row real sample: 3 W-zero, 2 W-copied-from-cumulative, 7 mismatches, 3 all-zero, 12 misclassified Deaf Reach rows. A plain sum of w_total (2,882) differs from the resolved Direct total (2,205).                                                            |
| **Form changes recorded** | 19 facility types (gia, SPDPA, dis_cer, legal support added); certificate and legal-support groups; indirect reach fields; primary-recipient question; GIS now required; rp_start relabelled as inception date; q_sections removed.                                                         |
| **Period logic**          | Period comes from rp_end only; rp_start is the inception date; overlap detection by rp_start is dropped.                                                                                                                                                                                    |
| **Diagnostics**           | Added: W zero or blank, W copied from cumulative, W versus section mismatch, all-zero report, misclassified type, near-duplicate names, contact field misuse, period meaning.                                                                                                               |
| **Breakdowns**            | New Section 5.6: tables by facility type, region (division) and district, with reconciliation to the grand total and reference numbers in tests/expected_breakdown.csv.                                                                                                                     |
| **Decisions**             | Added decisions 10 to 18 with defaults. Appendix A regenerated (143 number fields).                                                                                                                                                                                                         |
| **Project folder**        | Added the developer prompt v2, reference code, anonymised sample cases with expected results, and 38 test cases.                                                                                                                                                                            |

# Appendix D. Changes in Version 1.1 (from 1.0)

| **Area**         | **Change**                                                                                                                                                                           |
|------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Source audit** | Corrected: the form does have an optional geopoint (GIS). Added form fields that were missing from the audit (contact, ownership, R, Q, G1, H, I, K, L, M, P). Clarified row counts. |
| **KPIs**         | Replaced single-field rules with canonical coalesce rules, because w_new and w_waiting are not asked for every facility type. Added cumulative KPI.                                  |
| **Devices**      | Added an exact R / P5 field mapping and the one-source rule.                                                                                                                         |
| **Verification** | Separated Kobo \_validation_status from the form field verification_status.                                                                                                          |
| **GIS**          | Added coordinate source rules and status labels; proposed colour hex values and a colour-blind test.                                                                                 |
| **Routing**      | Added the 15 facility types with service categories and sections.                                                                                                                    |
| **Diagnostics**  | Replaced the generic list with concrete, testable rules using real field names.                                                                                                      |
| **Security**     | Restricted personal fields; hosting and sign-in decision added.                                                                                                                      |
| **New**          | Appendix A metric dictionary with unit and aggregation rule for all 127 integer metrics plus w_total; decision list with defaults.                                                   |
