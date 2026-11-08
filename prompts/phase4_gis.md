Phase 4: GIS.

Read `docs/00_specification.md` Section 7.

Task: build the Geographic Coverage page.
- Load boundary files from `data/boundaries/` if present. If the folder is empty, show a clear message and use a district table and bar view instead. Do NOT draw or approximate boundaries.
- Neutral grey division polygons with text labels (the old six division colours are retired). Marker colours by ownership per docs/gis_map_styling.md: government green, partner blue, other purple, unknown grey; service icons per docs/gis_icon_map.csv; icon + text always.
- Beside the map: main total (Direct), total indirect (Estimated x5), total reach, Direct by service type, and a Data received panel.
 Visible district outlines at all zoom levels.
- Facility pins only where the coordinate rules in 7.3 pass. No pins at guessed locations or centroids.
- Hover and click drill-down as specified. Clicking a district sets the global district filter.
- Accessible table alternative. Export map as PNG or HTML.
- Use the edge rows in the synthetic data (missing GIS, GIS outside Sindh) to test the rules.

Plan first, then wait for my approval.

Map filters: service type, ownership class, region, district (same filter bar). Map download: a JPG of the complete Sindh extent every time, with filtered markers, legend, filters, period, source and refreshed time, rendered on the server; test that zooming or selecting does not change the exported extent.
