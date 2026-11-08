# Final checklist (v1.3)

## Stack (tested to install together)
Python 3.11; Streamlit 1.67; pandas 3.x; numpy; plotly 7; folium 0.20 + streamlit-folium; geopandas 1.2 + shapely; httpx 0.28; openpyxl; XlsxWriter; Matplotlib; Pillow; kaleido; reportlab; python-dotenv; pytest. Install check done in a clean virtual environment on 7 Nov 2026. Pin exact versions in `requirements.txt` after Phase 1 (`pip freeze`).

## Data path
Kobo export-settings XLSX URL -> `src/ingest/kobo_live.py` -> schema check -> restricted columns removed -> resolution ladder -> pages. Tested with a mocked server and with the real 107-row export file. The live call itself needs the real token and could not be run from the documentation environment.

## Expected results on the 7 Nov export (`tests/expected_sample_107.json`)
107 rows; 106 service reports (Regional Director excluded). Direct 7,728; Indirect (x5) 38,640; Total 46,368. Plain sum of w_total would be 8,267 (wrong). 27 of 30 districts and 6 of 6 divisions have reported; missing: Kashmore, Sujawal, Tharparkar.

## Open items that need an answer from DEPD
1. Share the latest XLSForm (the export has about 660 columns not in the dictionary).
2. Add a facility ID or centre code to the form (12 groups of same-name reports; range 7,112 to 7,728).
3. Confirm ownership colours and supply an ownership register.
4. Confirm decisions 10 to 26 in `docs/open_decisions.md`.
5. Token: put it in `.env` yourself; rotate it if it was ever pasted into chat.
