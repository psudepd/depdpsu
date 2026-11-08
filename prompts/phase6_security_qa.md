Phase 6: Security, data quality and deployment.

Read `docs/00_specification.md` Sections 11, 12 and 14.

Task:
1. Roles: admin, manager, regional coordinator, viewer. Filter data on the server before it reaches the page. Restricted fields (contact_name, contact_info, signature, pictures, story files) only for admin and manager.
2. Build the Data Quality page with every check in Section 11.3. Each check needs a unit test using the edge rows in `data/synthetic_submissions.csv`.
3. Run an accessibility pass (keyboard, contrast, table alternatives, no colour-only meaning).
4. Test every Excel and JPG export (content equals the filtered screen, no restricted fields, header shows filters and refresh time) and the full-Sindh map JPG. Follow `docs/deployment.md`: test the Docker build and `docker compose up`, the health check, a schema-error screen, the stale-data banner and a token-rotation note. Write README setup and deployment instructions. List the open decisions from `docs/open_decisions.md` that still block production.
5. Final report: what works, what is placeholder, and what is blocked by missing inputs (token, registry, boundaries).

Plan first, then wait for my approval.
