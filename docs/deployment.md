# Build, run and move the dashboard

## Flow
Kobo form -> Kobo export-settings XLSX URL (saved export) -> `src/ingest/kobo_live.py` (download, schema check, strip restricted columns, cache) -> resolution rules (`tests/reference_resolution.py` as library code) -> Streamlit pages.

## Configuration (environment variables or `.streamlit/secrets.toml`)
| Name | Meaning |
|---|---|
| `KOBO_EXPORT_URL` | The export-settings `data.xlsx` URL (see `.env.example`) |
| `KOBO_API_TOKEN` | Kobo API token with read access to the asset. Needed unless the export allows anonymous access |
| `CACHE_TTL_SECONDS` | Default 900 (15 minutes) |
| `FAMILY_FACTOR` | Default 5 (admin setting) |
| `SANITY_CEILING` | Default 1,000,000 per integer field |
| `TZ` | Asia/Karachi |

## Run locally (development in Antigravity)
`pip install -r requirements.txt`, copy `.env.example` to `.env`, put the real token in it, then `streamlit run app.py`. Run `pytest` first.

## Run on a server (portable)
1. Copy the folder to the server. 2. Create `.env` from `.env.example`. 3. `docker compose up -d --build`. 4. Put HTTPS and the department sign-in in front (Nginx or Caddy reverse proxy to port 8501). 5. Check `/_stcore/health`.
To move to another server, repeat the same steps. Nothing is stored in the image; the only state is the cache volume.

## Things to know about the export URL
- The saved export setting fixes the columns. If someone changes the export settings in Kobo (labels instead of XML names, group prefixes, select_multiple format, "include all versions"), the loader raises a schema error. Keep the setting as it is: XML names, no group separator, select_multiple expanded, all versions off.
- The export is generated when requested and may take several seconds. The app caches it and keeps the last good copy, marked "stale", if Kobo is unreachable.
- The file includes contact, signature, picture and story columns. The loader removes them from the general data.
- The live call could not be tested from the documentation environment (no network and no token). The first live run must be checked by the developer; the loader is unit-tested with a mocked server.
- Rotate the token if it was ever pasted into chat or committed.
