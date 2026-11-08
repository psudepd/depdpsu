# MASTER PROMPT — DEPD Beneficiary Data Collection XLSForm (Version 7, Dashboard-Ready)

## 1. Role and Objective

Act as a senior **KoBoToolbox XLSForm Developer, Data Management Specialist and Government MIS Architect**.

Build a complete, validated, ready-to-upload KoBoToolbox XLSForm (.xlsx) for the **DEPD Beneficiary Data Collection Form — Version 7 (incl. NOWPDP)**, **Government of Sindh — Department of Empowerment of Persons with Disabilities (DEPD)**.

**Purpose:** collect facility-wise aggregate data (unique beneficiaries, workloads, cumulative achievements, waiting lists) from DEPD facilities and partner organisations, **in a structure a dashboard can read directly with no cleaning**.

The form must be: simple and fast for non-technical staff; usable on mobile and desktop; offline-capable; free of repeated questions; one flat submission (no repeats).

**Source of truth:** the attached Version 7 Word form. Keep every facility type and indicator in it. Where this prompt and the Word form differ, follow the "Decisions" in Section 3.

**Existing deployed form:** if an earlier XLSForm (v6) exists, **keep its existing `name` values unchanged** so old and new submissions share the same columns. Apply the naming convention (11.F) to new fields only. If any rename is unavoidable, list it in a rename table in the data dictionary.

---

## 2. Mandatory Design Rules

1. **Aggregate data only.** No beneficiary names, CNICs, personal phone numbers, home addresses, biometrics or individual disability histories. Official facility names, the reporting officer's designation and official office contact details are allowed.
2. **No repeat groups** (`begin_repeat`/`end_repeat`), rosters, or household records. One metric = one field.
3. **Age groups:** one `select_multiple age_groups` question, "Which age groups are covered?": 0–5, 6–12, 13–18, 19+ years. No numeric age breakdown (see Decision D3).
4. **Gender:** four integer fields (Male, Female, Transgender, Other / Not recorded) in Section W. The total is a `calculate` using `coalesce(${w_male},0)+coalesce(${w_female},0)+coalesce(${w_trans},0)+coalesce(${w_other},0)`, shown in a read-only `note`. Never ask staff to add anything.
5. **Numbers:** every count is `integer` with constraint `. >= 0` and message "Please enter zero or a positive whole number." Enter 0 where the service runs but nothing happened. Hide questions for services that are not provided; never ask for "N/A".
6. **Blank vs zero:** a hidden (non-relevant) section exports as blank = "not applicable"; 0 = "applies, none". The dashboard must treat these differently.
7. **Routing:** `facility_type` decides which section(s) appear (table in Section 5). Multi-programme organisations (C-ARTS, NOWPDP) use one `select_multiple` service question, and only the selected sub-groups appear. Use plain, non-nested groups, except the Yes/No gates in Q and R.
8. **No double counting:** a person receiving several services is counted once, in Section W. Sessions, devices, kilometres, packages, audits and applications are never added to beneficiary counts.
9. **One question, one place.** Active, New and Waiting-list headcounts are asked **only in Section W** (see D4). Section-level questions keep only cumulative figures and workload or programme-specific indicators. Do not add "must equal" constraints between two manually typed copies of the same number. Remove the duplicate instead.

---

## 3. Decisions (resolved conflicts in the earlier prompt)

| # | Decision | Reason |
|---|---|---|
| D1 | **District:** one dropdown of the 30 Sindh districts. **Division is auto-filled** from a `division` column in the districts choice list (`calculate` via `instance('districts')/root/item[name=${district}]/division`). No cascading dropdown. | Dashboard needs division roll-ups; staff only pick the district. Matches the Word form. |
| D2 | **Facility identity:** if DEPD supplies a facility master list, use `select_one facilities` (filtered by district) plus "Other". Otherwise use free text **and** instruct the dashboard to match on a cleaned name. | Free-text names create duplicate facilities in charts and trends. |
| D3 | **Age:** keep the checkbox question. State clearly in the data dictionary that it supports "age groups served" views only, not age distributions. If DEPD wants age charts later, add 6 integer fields (0–5, 6–12, 13–17, 18–24, 25–59, 60+) in Section W only, with a calculated total shown beside the gender total. | The Word form has numeric age bands but the prompt rules them out. This keeps the form simple and the trade-off visible. |
| D4 | **Active / New / Waiting list** live only in W. These are removed from C, N, T, U and the NOWPDP P0 block. P0 keeps only "unique beneficiaries served since establishment". NOWPDP capacity comes from Section B. C-ARTS V1–V5 and NOWPDP P2/P3 keep their programme-level active and waiting figures because they describe a single programme, not the facility total. | Removes the duplicates the earlier prompt asked for and then tried to reconcile. |
| D5 | **GPS:** one optional facility-level `geopoint` in Section A (for the dashboard map). No GPS for people or households. | "No GPS" was meant for beneficiaries. A facility map needs a facility location. |
| D6 | **Section S** keeps the Word form's optional pictures (max 5, with caption and consent) and optional success-story PDF, plus short free-text boxes for "major achievements" and "main challenges". Remarks is a single optional box at the end. | Preserves V7 content, adds the narrative fields. |
| D7 | **Assistive devices:** Section R is for every facility type except NOWPDP. NOWPDP reports devices only in P5. A `kpi_dev_*` calculate layer (Section 12) combines both so the dashboard has one device column per type. | Avoids typing the same device counts twice. |
| D8 | **Word-form glitches to correct in the XLSForm:** in Sections C and N, "Services provided (tick)", "Support offered (tick)" and "Remarks" show "Number" as the response. Treat them as `select_multiple` and `text`. The document header still says "Version 5". | These are typos in the document. |

---

## 4. Required Worksheets

**survey:** `type | name | label | hint | required | relevant | constraint | constraint_message | calculation | default | appearance | choice_filter | parameters | media::image`
Use plain `label` (not `label::English`) so it matches the settings language.

**choices:** `list_name | name | label` (+ `division` for districts, + any filter columns used).

**settings:** `form_title | id_string | version | default_language`. English default. Keep the existing `id_string`; set `version` to `7.0`.

Add two extra worksheets (Kobo ignores them): **`data_dictionary`** and **`test_checklist`** (Section 13).

---

## 5. Section Structure and Routing

Order in the form: A, B, C, G1, H, I, K, L, M, N, Q, R, T, U, V, P, W, S, Declaration. Keep the Word section codes.

| Facility type (choice name) | Sections shown |
|---|---|
| `rcmhc`, `rcph` | A, B, C, R, W |
| `gov_se` (all Govt SE & Rehab Centre / Complex / VI&HIC / HIC / VIC / PD / ID; subtype recorded in M) | A, B, C, M, R, W |
| `pcrdp` | A, B, G1, R |
| `ipmr` (Institute of Physical Medicine & Rehabilitation) | A, B, L, R, W |
| `inclusive` (Director Inclusive Education / IEISU / inclusive schools) | A, B, N, R, W |
| `hostel` | A, B, I, R, W |
| `vtc` (Govt VTC, VR&E, Voc. Trg. & Rehab Centre) | A, B, K, R, W |
| `academy` | A, B, H, R, W |
| `deaf_reach` | A, B, T, R, W |
| `sipmr` | A, B, L, U, R, W |
| `carts` | A, B, V (V1–V5 selected), W, plus Q only if partner support is given, R |
| `nowpdp` | A, B, P (P0–P5 selected), W (R not shown, see D7) |
| `assistive_ip` | A, B, R |
| `regional_dir` | A, B (administrative: no beneficiary counts) |

All types end with S and the Declaration. Show W only for types marked W. Use `selected('a b c', ${facility_type})` for multi-value routing to keep expressions short.

---

## 6. Section A and B

**A, Facility & Reporting:** facility name (or facility list, D2), district, auto division, taluka (optional), union council (optional), reporting period start and end (`end >= start`, both `<= today()`), contact person name, designation, official email / contact number, submission date (`>= end`, `<= today()`), optional facility geopoint. Hint: *One submission = one facility = one reporting period.*

**B, Facility Type & Operational Profile:** facility type (all types in Section 5), C-ARTS sub-programmes (if `carts`), NOWPDP programmes (if `nowpdp`: Shanakht, Taleem, Hunar, Rozgar, Suvaari), operational status, ownership (Government / Partner organisation / Other), services provided during period (Yes/No), services available (checkboxes), services free of charge (Yes / No / Partly), approved beneficiary capacity (integer, optional).
The "active waiting list exists" Yes/No is **dropped**. It is implied by the Section W waiting count.

---

## 7. Facility Sections (keep all Word V7 indicators, subject to D4/D8)

- **C:** cumulative served; completing rehabilitation/education; services provided (checkboxes); RCMHC multidisciplinary children; RCPH mobility-training patients and fitted devices.
- **G1:** services (checkboxes); registrations received / approved / rejected / pending; certificates issued; complaints received / resolved. **No cross-field constraints** (resolved cases can come from earlier periods).
- **H:** course types; completed; dropped out; trainers present.
- **I:** hostel type; services given. (Beds = Section B capacity.)
- **K:** trades offered; services given; completed; dropped out; placed in jobs.
- **L** (`sipmr`, `ipmr`): OPD visits; assessments; referrals; services given; therapy types; main shortages.
- **M:** centre type; units; education levels; therapy services. No people counts.
- **N:** integrated (cumulative); schools registered; graduated; teachers trained (ToT); new integrations; monitoring visits; support offered. `n_enrolled <= n_integrated` is allowed only if both are kept.
- **Q** (C-ARTS, gated by "Did you give partner support outside your direct services?"): type of support; sections covered; people reached by gender (4 fields); groups reached; age groups; disability types.
- **R** (gated by "Were assistive devices given?"): organisation, project, DEPD support (Yes/No/Partly), grant year, districts, recipients by gender (4), age groups, disability types, and device quantity fields (wheelchair, crutches/sticks, walker, prosthesis, orthosis, hearing aid, spectacles/low-vision, other with "specify" shown only when > 0). Device defaults = 0.
- **T:** cumulative enrolled; graduates placed; awaiting placement; transport users; daily KM; teachers trained; PSL words.
- **U:** all 16 SIPMR indicators, except active / new / waiting, which come from W. Keep physiotherapy, OT and speech patients and sessions as separate fields, plus prosthetic / orthotic made, fitted, repaired and awaiting.
- **V1–V5 (C-ARTS):** only selected sub-programmes appear. Keep every Word indicator. Parent trainees (V5) never enter the W total.

## 8. Section P — NOWPDP

Shown when `facility_type = nowpdp`. Show only the programmes ticked in Section B.

- **P0:** Total unique beneficiaries served since establishment (one field). Active, new and waiting come from W. Capacity comes from B.
- **P1 Shanakht:** CNICs facilitated (cumulative); applications initiated; CNICs issued; pending with NADRA / Social Welfare; legal guidance only.
- **P2 Taleem:** integrated since inception; active enrolled (`<=` integrated); out-of-school waiting; school packages (items); passed / graduated.
- **P3 Hunar:** certified (cumulative); active trainees; waiting applicants; completed; dropped out; courses offered (`select_multiple nowpdp_courses`: IT & Computer, Tailoring, Graphic Design, Call Centre, English Language, Mobile Repairing, Other).
- **P4 Rozgar:** corporate/banking placements (cumulative); placements in period; job-seekers awaiting; self-employment / small enterprises; accessibility audits and sensitisation sessions. Counts of people stay separate from counts of audits and sessions.
- **P5 Suvaari:** unique individuals given devices (cumulative); unique fitted in period; awaiting measurement / fabrication; manual wheelchairs; motorised tri-wheelers; crutches/sticks/walkers; hearing aids; white canes / low-vision aids; other; remarks. One field per device type. Note: "Device quantities are not people."

## 9. Section W — Global Unique Beneficiary Summary

Shown for all direct-service types (Section 5). Fields: Male, Female, Transgender, Other / Not recorded (all "Active at reporting end date"); calculated total with note; age groups covered (checkboxes); disability types served (checkboxes, one question for the whole facility); unique new beneficiaries registered in period; unique people on waiting list at reporting end date.
This is the **only** place for these headcounts.
For C-ARTS, exclude parent and caregiver trainees unless they independently qualify.
For NOWPDP, W is the master headcount. Do not add programme headcounts together.

## 10. Section S and Declaration

**S (optional):** achievements, challenges, pictures (Yes/No, count 1–5, up to 5 images with `max-pixels=1024`, one caption, consent confirmation = Yes required), success story (Yes/No, title, PDF, permission). Reminder: *pictures and stories do not replace the numbers; no names, CNICs, phones or addresses visible.*

**Declaration (last):** one optional Remarks box; acknowledgement ("figures are accurate, numbers only, and people receiving several services are counted once"); reporting officer signature; declaration date (default `today()`); verified-by name (Director / Regional Director); verification status (Verified / Not verified).

---

## 11. Data Quality Rules

**A. Definitions in hints:** Cumulative = since establishment. Active = receiving services at the reporting end date. New = first registered during the reporting period. Waiting list = people still waiting at the reporting end date. Sessions = sessions, not people. Devices = quantity, not people.

**B. Dates:** all "during period" indicators refer to the Section A dates. State this once in the form introduction, not in every hint.

**C. Validation (only where the definitions truly match):** `end >= start`; `submission >= end`; active `<=` cumulative within the same programme (V1–V5, P2, N); all integers `>= 0`. **Do not** compare cumulative figures with period workloads, and **do not** add a "gender total = headcount" check (the total is calculated).

**D. No duplication:** see rule 9. Totals are calculations, never typed twice.

**E. Navigation:** short group labels, one main group per facility type, no deep nesting.

**F. Naming convention for new fields:** lowercase, underscores, section prefix, no spaces. Examples: `facility_type`, `district`, `w_active_total`, `p0_cumulative`, `p1_shanakht_cnic_issued`, `p2_taleem_active`, `p3_hunar_active`, `p4_rozgar_placements`, `p5_suvaari_wheelchairs`. Names must be unique across the form.

**G. Privacy:** no personal identifiers anywhere (including image and file fields: remind staff to hide identifying details).

**H. Offline:** no `pulldata()` from external files, no API calls. Use choice lists and `instance()` on internal choices only.

---

## 12. Dashboard Layer (the main addition)

Add a final hidden group of `calculate` fields so the dashboard needs no per-facility logic. All are blank when not applicable.

| Field | Purpose |
|---|---|
| `reporting_year`, `reporting_quarter`, `reporting_month` | From `rp_end` (`format-date(${rp_end},'%Y')`; quarter = `int((int(format-date(${rp_end},'%m'))+2) div 3)`). Enables trends. |
| `division` | Auto from district (D1). |
| `submission_key` | `concat(${facility_code_or_name},'_',format-date(${rp_end},'%Y-%m-%d'))`. The dashboard keeps only the **latest** submission per key. Kobo cannot block duplicates. |
| `kpi_cumulative` | `coalesce(c_cumulative, n_integrated, t_cum, u_cum, p_cum)`. C-ARTS is excluded because V1–V5 overlap. |
| `kpi_dev_wheelchair`, `kpi_dev_crutches`, `kpi_dev_walker`, `kpi_dev_limb`, `kpi_dev_orthosis`, `kpi_dev_hearing`, `kpi_dev_vision`, `kpi_dev_other` | One device total per type, combining Section R and NOWPDP P5. Never typed twice (D7). |

The dashboard reads Active, New, Waiting and gender from the Section W fields directly (`w_active_total`, `w_new`, `w_waiting`, `w_male`, `w_female`, `w_trans`, `w_other`).

**The form must support these dashboard views** (describe them in the data dictionary; do not build the dashboard):
1. **Overview:** facilities reporting vs expected, unique active, new, waiting, by division / district / facility type / period.
2. **Gender and coverage:** gender split; age groups and disability types served.
3. **Service workload:** sessions, devices, trainings, placements, KM, packages, kept separate from beneficiary counts.
4. **Programmes:** C-ARTS V1–V5, NOWPDP P1–P5, Deaf Reach, SIPMR, Inclusive Education.
5. **Data quality:** submissions per period, verification status, late submissions, blank-vs-zero completeness.

Note for the data dictionary: Kobo exports each checkbox answer as separate 0/1 columns, and an export with no repeats is a single flat table that BI tools can read directly.

---

## 13. Deliverables

1. The complete `.xlsx` XLSForm (`survey`, `choices`, `settings`), with all facility types and sections above.
2. `data_dictionary` sheet: field name, section, definition, unit (people / sessions / devices / KM / items), period type (cumulative / current / during period), and whether it counts toward beneficiary totals (Y/N).
3. `test_checklist` sheet: one row per facility type and per NOWPDP and C-ARTS sub-programme, listing which sections must appear and hide, plus checks for dates, calculated totals and gates.
4. A short change log vs the earlier form, and any rename table (Section 1).

**Validate before delivering:** convert with pyxform (zero errors and warnings) and preview in Kobo; check every `select_*` list exists; every `${field}` reference exists; every `begin_group` has an `end_group`; relevance expressions parse; choice names are unique per list and have no spaces.

**Do not deliver a partial or sample form.**

## Final Design Principle

**One facility → one reporting period → relevant service questions → one unique-beneficiary summary → declaration.** Ask every number once, calculate every total, and keep the structure flat so the dashboard works without cleaning.
