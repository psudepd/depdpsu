# KPI rules (authoritative, short form)

Full reasoning: `00_specification.md` Section 5. Reference code: `tests/reference_resolution.py`. If this file and the specification differ, stop and ask.

## Headline: Direct, Family (indirect) and Total reach
Basis toggle: **Active** (default) or **Cumulative**.

| Number | Formula |
|---|---|
| Direct | resolved unique persons per facility, summed across facilities |
| Indirect (family) | Direct x F, F = 5 (admin setting). Always labelled "Estimated" |
| Total reach | Direct + Indirect = Direct x (1 + F). Always labelled "Estimated" |
| Reported indirect reach | `Total_indirect_reach_since_inception`, `Beneficiary_students_inception_In_Direct`, `Total_Indirect_Reach_ablishment_Indirect`. Separate card, cumulative only. NEVER added to the three numbers above |

## Resolving Direct (Active basis), per submission
`W` = `w_total`, `S` = section-level active figure, `C` = cumulative figure.
1. `pcrdp`, `regional_dir` -> Not applicable. `assistive_ip` has no W: Direct = people who received devices in the period (R male + female + transgender + other), flagged `period_count_not_stock` (decision 23).
2. `W` > 0 and W is not a copy of C (W = C while S exists and S != C) -> use W. If S > 0 and the difference is above 20% -> flag `review`.
3. Else `S` > 0 -> use S; flag `W_blank` / `W_zero` / `W_copied_from_cumulative`.
4. Else W = 0 or S = 0 -> 0, flag `all_zero_report` (low confidence).
5. Else -> No data.

| facility_type | S | C |
|---|---|---|
| rcmhc, rcph, gov_se, gia, pcrdp | c_active | c_cumulative |
| inclusive | n_enrolled | n_integrated |
| carts | max(v1..v4_active), lower bound; V5 parents excluded | none |
| nowpdp | max(p2_active, p3_active), lower bound | p_cum |
| deaf_reach | none | t_cum |
| sipmr | none | u_cum |
| dis_cer, sindh_persons_with_disabilitie | none | Cumulative_Disabilit_sued_Since_Inception |
| legal_support__beneficiaries | none | Total_Direct_Benefic_since_establishment |
| hostel, vtc, academy, ipmr | none | none ("Not collected") |

Cumulative basis: first non-blank C only. W is never used.

## Other KPIs
| KPI | Formula | Aggregation |
|---|---|---|
| New beneficiaries | `coalesce(w_new, c_new, n_new)` | Sum over distinct reporting periods (by `rp_end`) |
| Waiting list | `coalesce(w_waiting, c_waiting, n_waiting)` | Latest snapshot per facility |
| Gender | `w_male, w_female, w_trans, w_other` | Latest snapshot; use only when W passed rule 2 (otherwise "Gender not reported") |
| Devices distributed | see `device_mapping.csv` | Sum of FLOW; NOWPDP uses P5 only, others use R only |
| Reporting facilities | distinct `facility_id` with an accepted submission | Needs registry; otherwise label "unverified" |
| Coverage % | reporting / expected x 100 | Only when an expected-facility denominator exists |

## Breakdowns
By facility type (as filed; optional reviewed overrides), by division (from the district mapping, never the submitted division) and by district. List all 18 services (regional_dir excluded), 6 divisions and 30 districts; empty ones show "No reports". Each table reconciles to the grand total.

## Rule codes in `field_dictionary.csv`
`CUM` latest cumulative snapshot per facility; `SNAP` latest snapshot at reporting end date; `FLOW` sum over distinct reporting periods.

## Hard rules
1. Blank = not applicable. `0` = applies, none. Never convert blank to 0.
2. Never total across different units (people, sessions, visits, devices, items, km/day, schools, cases, certificates).
3. Never add reported indirect reach, devices, sessions, certificates or C-ARTS V5 parents to Direct.
4. Period = `rp_end` (year, quarter, month). `rp_start` is the facility inception date, not a period start. Key = facility_id + `rp_end`; latest `_submission_time` wins; keep older revisions in an audit view.
5. Accepted = Kobo `_validation_status` is Approved (if the review workflow is used). Show form `verification_status` separately.
6. Totals across facilities are labelled "sum of facility-reported unique headcounts". The family estimate is labelled "Estimated".
7. Use Asia/Karachi for all period boundaries.


**Regional Director (`regional_dir`) is office information only:** exclude it from service lists, beneficiary totals and service counts; show it only in the admin Offices view and as a green dashed office marker. Add the Summary Reports tab described in prompts/dashboard_developer_prompt_v2.md section 4F.
