# GIS map styling: colour = ownership class, shape = service category, icon = service (v1.3)

## 1. Colour = ownership class, fixed by service type (DEPD rule)
The class comes from `data/ownership_by_type.csv`, not from the submitted `ownership` field.
| Class | Colour | Hex | Service types |
|---|---|---|---|
| Government | Green | #2E7D32 | RCMHC, RCPH, government special education (gov_se), C-ARTS, vocational training centre (vtc), SPDPA, disability certificate (dis_cer), inclusive education, Regional Director |
| Partner organisation | Blue | #1F5FBF | Assistive devices (assistive_ip), GIA, Deaf Reach |
| Other | Purple | #7B3FA0 | All remaining types: SIPMR, IPMR, hostel, academy, NOWPDP, PCRDP, legal support (proposed; DEPD to confirm) |
| Unknown type | Grey | #6B7280 | Facility type missing or not in the table |

## 2. Shape = service category (so education, health and training look different even without colour)
| Category | Marker shape | Icon inside (by service) | Types |
|---|---|---|---|
| Health / rehabilitation | Circle | medical cross | rcmhc, rcph, sipmr, ipmr |
| Education / school | Rounded square | school building (gov_se, Deaf Reach), book (inclusive), book + hand (GIA) | gov_se, inclusive, deaf_reach, gia |
| Training / vocational | Hexagon | tools (C-ARTS, VTC), graduation cap (academy), briefcase (NOWPDP) | carts, vtc, academy, nowpdp |
| Hostel / residential | House (pentagon) | bed | hostel |
| Assistive devices | Triangle | wheelchair | assistive_ip |
| Registration / legal | Diamond | identity card, scales | sindh_persons_with_disabilitie, dis_cer, legal_support__beneficiaries, pcrdp |
| Office (not a service) | Square with dashed outline | office building | regional_dir |
Full table with hex codes: `docs/gis_icon_map.csv`. Shape + icon + colour + a text label are always shown together; the legend shows all four. A multi-service facility keeps its primary shape and adds a small multi-service badge.

## 3. Rules
- Division polygons use neutral grey tints only (#EEF1F4 / #E3E8ED) with dark outlines, so green / blue / purple belong to ownership alone.
- White icon on each fill must reach contrast 4.5:1; test the three colours with a colour-vision simulator. Shapes carry the category, so colour-blind users can still tell health, education and training apart.
- The submitted `ownership` field is only a check. When it differs from the class of the type (for example 37 of 58 gov_se reports say partner; 20 of 25 Deaf Reach say other), keep the class colour and show "submitted ownership differs" in Data Quality. Never recolour silently.
- A reviewed facility-level override (`facility_id -> class`) wins over the type rule when DEPD supplies one.
- If a "with suggested corrections" view moves a gov_se report named "Deaf Reach" to deaf_reach, its colour changes from green to blue with it.
- Regional Director: green dashed office marker, shown in the admin Offices view; never counted as a service or in totals.

## 4. Map panels (same page as the map)
1. Headline: Main total beneficiaries (Direct), Total indirect beneficiaries (Estimated, x5), Total reach (Estimated).
2. Direct by service type: one card or bar per service (18; "No reports" where none) with its shape, icon and colour, Direct, reports, male / female / other where W was usable, new, waiting.
3. Data received: reports, facilities, districts reporting x of 30, last submission (Asia/Karachi), source mix, latest 10 reports (no contact or personal fields).
4. Filters above the map: service type, ownership class, region, district (same filter bar as every other tab). Clicking a marker or card filters every panel. All panels follow the global filters and the Active / Cumulative toggle.

## 5. Map download
Every download is a JPG of the complete Sindh extent (total bounds of the approved boundary file plus a margin), independent of zoom, pan or selection. It shows the filtered markers, legend (colour, shape, icon), title, active filters, period, source and refreshed time (Asia/Karachi). Rendered on the server (GeoPandas + Matplotlib); see `src/export/exporters.py::sindh_extent`.
