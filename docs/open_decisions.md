# Open decisions (defaults the agent must use until the owner answers)

| # | Decision | Default |
|---|---|---|
| 1 | Kobo server, token permissions, asset UID, group prefixes (real exports have none) | Placeholder in `.streamlit/secrets.toml.example`; use the synthetic file and `tests/sample_cases.csv` |
| 2 | District boundary GeoJSON and facility registry with coordinates | District-only map; no pins; do NOT draw guessed boundaries |
| 3 | Reporting cadence and expected-facility denominator | Period from `rp_end`; no coverage % |
| 4 | Canonical version name (Word form header says "Version 5") | Use "Version 7" |
| 5 | True age distribution needs numeric age counts in the Kobo form | Age and disability are coverage only |
| 6 | Device source (R vs P5) | P5 for nowpdp, R for others |
| 7 | Cross-facility deduplication | Label totals "facility-reported" |
| 8 | Hosting and sign-in | Private deployment with real sign-in |
| 9 | Urdu labels | English only |
| 10 | Total reach = Direct + Direct x 5, or Direct x 5 only | Direct + Direct x 5 |
| 11 | Family factor F | 5 (admin setting) |
| 12 | Facility-reported indirect reach replaces the x5 estimate? | No, shown separately |
| 13 | W vs section figure differ by more than 20%: which one? | Keep W, flag for review |
| 14 | Do dis_cer, SPDPA and legal-support facilities fill Section W? | Yes for now; they use the Cumulative basis |
| 15 | `rp_start` meaning (form label now says inception date) | Inception date; period from `rp_end` only |
| 16 | PCRDP vs SPDPA: PCRDP still shows Section C and no G1 | Treat as in the form; flag in diagnostics |
| 17 | Auto-generated field names (`group_dp8mz64`, `Cumulative_Disabilit_...`, `legal_support__beneficiaries`) | Use as exported; map in the field dictionary |
| 18 | Meaning of the primary-recipient question (Outreach vs Internal) | Report Outreach and Internal separately; never add Internal to Direct |
| 19 | Ownership class by service type (DEPD rule, `data/ownership_by_type.csv`): government = RCMHC, RCPH, gov_se, C-ARTS, VTC, SPDPA, disability certificate, inclusive, Regional Director; partner = assistive devices, GIA, Deaf Reach; others purple (to confirm) | Colour by the DEPD rule; submitted ownership is a check only |
| 20 | Kobo export access: token owner, anonymous access or not, who may change the export setting | Token in secrets; schema check on every load |
| 21 | Hosting target and sign-in for live deployment | Docker on a DEPD or cloud server, private network, sign-in |
| 22 | `regional_dir` is office information only | Excluded from services, totals and counts |
| 23 | Do Assistive Devices (assistive_ip) recipients count as Direct? | Yes, from Section R recipients, flagged as a period count (208 in the 107-row export) |
| 24 | Same centre name in the same district and month: duplicate or different centres? Add a facility ID / centre code to the form? | Count all; flag groups; admin can mark reviewed duplicates |
| 25 | SPDPA row filed by an NGO (Ida Rieu): wrong facility type? | Keep value, flag "type may be wrong" |
| 26 | The form has grown (about 660 columns are not in the field dictionary, including a rewritten assistive-device section R1 to R5 that is still empty). Share the latest XLSForm so the dictionary is regenerated | Loader ignores unknown columns with a warning; Phase 1 reports the differences |
