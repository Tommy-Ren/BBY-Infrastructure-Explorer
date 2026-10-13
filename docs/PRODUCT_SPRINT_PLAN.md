# Burnaby School Infrastructure Explorer: product sprint plan

**Status:** proposed roadmap, 13 October 2026  
**Planning assumption:** one developer, six two-week sprints at roughly 8–12 hours per week. Re-estimate after Sprint 1.  
**Starting point:** the completed CMPT 353 analysis and report; the course-era plan remains in `temp/sprint plan.md` for historical context.

## Product goal

Turn the reproducible analysis into a public, usable application for exploring the *recorded presence* of traffic-calming infrastructure around Burnaby schools. A visitor should be able to find a school, see nearby infrastructure on a map, understand the 100 m / 250 m / 500 m coverage measures, and compare schools without reading a PDF or running Python. A planning-oriented user should be able to download the displayed data and see when it was retrieved and how the measures were calculated.

The portfolio story is an end-to-end data product: municipal data ingestion, validated geospatial analysis, a documented API, an accessible interactive frontend, automated checks, and a deployed demo. Keep the original report and snapshot reproducible while developing the app.

**Product language:** “coverage” means a feature recorded within a straight-line radius of a school point. It does not measure walking distance, student exposure, collisions, or whether a school is safe. Clusters describe similar infrastructure patterns, not safety grades. Show this distinction beside the relevant UI, not only in a footer.

## Current assets and gaps

| Existing asset | Where it lives | Product implication |
| --- | --- | --- |
| Four downloaded City of Burnaby ArcGIS layers with a retrieval manifest | `data/raw/`, `src/download_*.py` | Use the included snapshot as the first demo dataset; show its retrieval date and source. |
| Cleaned projected GeoJSON and quality summary | `data/processed/`, `src/clean_*.py` | Keep measurements in EPSG:26910 (metres); convert map/API geometry to WGS84 coordinates. |
| School-level distances, counts at 100/250/500 m, statistical summaries, PCA and clusters | `output/tables/`, `src/analyse_*.py`, `src/cluster_*.py` | Expose validated school details and analysis, with plain-language explanations. |
| Six report figures and a PDF | `output/figures/`, `report.pdf` | Use as methodological reference and portfolio context, not as the primary interface. |
| No web app, HTTP API, automated test suite, or deployment configuration visible | Repository inspection | Build one complete user journey before adding optional features. |

Two issues affect future refreshes. `src/clean_config.py` fixes the expected school count at 64, and `src/clean_layers.py` derives `school_id` from the City's `OBJECTID`; the README says these IDs can be reassigned. Preserve source IDs for provenance, but introduce an application-owned stable identifier and record how matches across snapshots are reviewed. Treat a changed school count as a reviewable validation result rather than silently accepting or rejecting it.

Before naming a count “active infrastructure,” review service-status semantics: `src/analyse_distances.py` excludes removed traffic signals, while `src/analyse_summaries.py` currently counts all cleaned traffic-calming features. Resolve that difference in the data contract and regression tests, then use wording in the UI that matches the chosen rule. The local workspace also has no Git metadata; establish or connect version control before configuring CI.

## MVP and technical direction

**MVP journey:** open the site → search for a school → select it on the map or list → see its nearest recorded features and counts at the three existing radii → inspect methodology, source date, and data limitations → share the selected school URL. This journey is the release gate. Search, map, and a school detail panel should all work on desktop and mobile.

Suggested implementation, to be confirmed during Sprint 1:

| Layer | Choice and reason |
| --- | --- |
| Frontend | React + TypeScript with [Vite](https://vite.dev/guide/) for a small client app and production build. Use [MapLibre GL JS](https://maplibre.org/maplibre-gl-js/docs/) for map layers, markers, and feature interactions. |
| Backend | Python [FastAPI](https://fastapi.tiangolo.com/features/) to reuse the existing pipeline, validate response models, and publish OpenAPI documentation. Separate API code from the existing command-line scripts. |
| Data for the first release | Load a versioned, validated export of the existing CSV and GeoJSON outputs at startup; serve read-only data. This is enough for the current 64-school dataset and keeps the first release achievable. |
| Spatial database decision | Add PostgreSQL/PostGIS only if measured query latency, refresh needs, or new spatial filters justify it. For indexed radius queries, [PostGIS `ST_DWithin`](https://postgis.net/docs/ST_DWithin.html) is an option. Record the decision and avoid a database migration as a prerequisite for the MVP. |
| Deployment | Host the static frontend and containerized API, with HTTPS, health checks, pinned dependencies, and documented environment variables. Choose a provider after checking cost and free-tier limits at deployment time. |

Start with a small read-only API contract: `GET /health`, `GET /api/v1/datasets/current`, `GET /api/v1/schools?search=&limit=&offset=`, `GET /api/v1/schools/{id}`, and `GET /api/v1/features?bbox=&type=`. Define bounds and pagination so a malformed or unbounded request cannot load the whole source layer. School detail should include WGS84 location, original-source identifier, distances and units, counts by radius, nearest feature details, cluster label **only when clearly explained**, and dataset version. Use `404` for unknown schools and consistent validation errors. Keep report-level statistical comparisons as a separate, later endpoint if the UI needs them.

Suggested repository layout after Sprint 1: `src/` remains the analysis pipeline; add `backend/` for API and export code, `frontend/` for the web app, `tests/` for pipeline/API tests, and `docs/` for design, data, deployment, and sprint notes. Do not move the original scripts merely to achieve a new directory shape.

## Sprints

Each sprint ends with a working demonstration and a short note recording what shipped, what changed, and what blocked the next sprint. The deliverables below are ordered by dependency, but UI design and data review can overlap.

### Sprint 1 — Define the product and make a trustworthy data contract

**Outcome:** a developer can regenerate an app-ready snapshot and call a local API for one school.

- Write a one-page product brief with primary audience, MVP journey, low-fidelity desktop/mobile wireframes, and a small design system (type, colour, spacing, map legend).
- Document the current fields, source URLs, retrieval timestamp, straight-line distance method, CRS conversion, missing-value rules, and how a school ID is matched across snapshots.
- Decide and document which traffic-calming service statuses belong in coverage counts, reconcile the analysis and UI label, and add a regression test for the rule.
- Initialize or reconnect the source repository if needed, so later CI and release work has a versioned history.
- Set up minimal CI for the data-contract and API tests once the repository is connected; expand it with frontend checks in later sprints.
- Build a deterministic export from the existing pipeline outputs into a single versioned app dataset. Include row counts, a checksum/manifest, schema version, and data-quality summary. Do not refresh the municipal data as part of reproducing the original report.
- Add focused tests for school count/ID handling, join completeness, unique IDs, nonnegative distances, monotone radius counts, and EPSG:26910 → EPSG:4326 coordinate conversion. Resolve the hard-coded `64` as a configurable snapshot expectation or review gate.
- Implement FastAPI response models and the read-only dataset, school-list, and school-detail endpoints. Generate OpenAPI; add API tests for expected, missing, and invalid requests.

**Done when:** a clean checkout can follow written setup commands, regenerate the app dataset from the committed snapshot, run the API, and pass the data-contract/API tests. A school in the API matches the corresponding CSV row and maps to a valid Burnaby-area longitude/latitude.

### Sprint 2 — Ship the first full-stack journey

**Outcome:** a visitor can explore an actual school through a working map and detail view.

- Build a responsive app shell with search, school list, map, selected-school panel, three radius choices, legend, and clear loading/empty/error states.
- Connect the frontend to the API; keep selected school and radius in the URL so a link survives reload and can be shared.
- Display school points and nearby traffic-calming features; make school selection possible from the list and map. Ensure the list works when the map cannot load.
- Present the count and nearest-feature distance with units, a source date, attribution, and an inline statement that the radius is straight-line distance.
- Deploy a preview of both services; set the correct API origin/CORS policy and document local run commands.

**Done when:** the MVP journey works from a clean browser on desktop and a narrow mobile viewport, links reopen the same school, API errors have a usable retry path, and the preview URL is accessible outside the developer machine. This is the first portfolio demo.

### Sprint 3 — Comparison and explanation

**Outcome:** users can compare schools without mistaking infrastructure counts for a safety ranking.

- Add table sorting and filters for name, radius count, and nearest-feature distance, backed by the API if needed. Keep table and map selection synchronized.
- Add a two-school comparison view with the same units and dataset version. Show both distance and count; do not collapse them into a single “safety score.”
- Add a methodology page explaining source layers, thresholds, how missing/removed records are treated, cluster meaning, and limits of the school-vs-other-place statistical comparison.
- Add CSV export for the currently filtered school rows, with a data dictionary and a visible dataset version. Keep map feature queries bounded to the viewport.
- Review labels and a few representative schools against the original outputs; correct any mismatches before expanding the UI.

**Done when:** a user can compare two schools, reproduce a displayed value from a downloadable row, and find an explanation for every metric exposed in the UI. Search, filters, and shareable URLs remain usable with keyboard only.

### Sprint 4 — Refreshable data and operational safeguards

**Outcome:** new City data can be evaluated and published without corrupting the public snapshot.

- Build a refresh command that downloads to a staging directory, runs cleaning and analysis, validates schemas/counts/geometry/IDs, produces an immutable version, and emits a human-readable change report.
- Implement a manual promote/rollback step. Keep the last known good dataset available if retrieval or validation fails. Show current version and retrieval time through `/api/v1/datasets/current`.
- Add checks for changes in municipal codes/labels, duplicate or shifted school points, unexpected row-count changes, and invalid geometries. Document how ambiguous school-ID matches are resolved.
- Measure startup time, response time, and payload size with real snapshot data. Cache or simplify geometry only if these measurements show a need; evaluate PostGIS here if query requirements have grown.
- Separate the original report snapshot from the live-app dataset so a refresh never rewrites the course results.

**Done when:** one staged refresh can be reviewed and promoted, a bad download cannot replace production data, and rollback restores the previous version. The published API identifies exactly which snapshot supplied a response.

### Sprint 5 — Quality, accessibility, and security

**Outcome:** the app feels dependable under normal use and understandable to nontechnical visitors.

- Add unit tests for transformation rules and API contracts; add a small set of browser end-to-end tests for search → select → compare → share. Test failure and empty states, not only the happy path.
- Check keyboard navigation, visible focus, form labels, contrast, reduced motion, and screen-reader names. Provide a textual alternative to map-only information.
- Add request bounds, timeouts, restrained CORS origins, dependency scanning, no committed secrets, and sensible HTTP security headers. Since the first release is public and read-only, avoid accounts and personal data unless a later feature requires them.
- Run formatter/linter/type checks and tests in CI; build the frontend and image on each change. Write a brief release checklist and an incident/rollback note.
- Conduct a small usability review with 2–3 people unfamiliar with the project; record concrete friction and fix the most severe issues.

**Done when:** CI passes, the three principal flows work in current desktop/mobile browsers, the accessibility checklist has no blocking issues, and major usability findings are resolved or explicitly scheduled.

### Sprint 6 — Public launch and resume presentation

**Outcome:** a reviewer can try the product, understand its technical work, and verify the analysis.

- Deploy production frontend and API with a stable URL, HTTPS, health checks, basic uptime/error monitoring, and a tested rollback procedure. Confirm hosting cost and limits before selecting a service.
- Rewrite the README for the live product: problem, screenshot/GIF, demo URL, architecture, data flow, setup, tests, API docs, source attribution, methodology limits, and links to the original report.
- Add an architecture diagram, two concise technical case-study paragraphs (one data challenge, one application challenge), and a short demo script that reaches the key screen in under two minutes.
- Capture evidence for portfolio claims: number of records and schools in the published snapshot, successful CI run, measured response times under stated conditions, and an accessibility/usability review. Write resume bullets using only verified numbers.
- Smoke-test the deployed site from a new device or browser profile, check attribution and dataset freshness display, and tag a release once the checks pass.

**Done when:** the public URL, API documentation, README, demo media, and reproducibility instructions all work; a reader can trace a displayed value to a dataset version and the original source.

## Definition of done for every feature

- User-visible behaviour works on desktop and mobile and has loading, empty, and error handling.
- API response fields have names, units, and documented meaning; geometry coordinates are explicitly identified by CRS.
- A displayed statistic can be traced to a tested transformation and a versioned source snapshot.
- Any claim about school safety or causal effects is removed or qualified according to the available data.
- Relevant checks pass in CI, and the feature is demonstrated before marking its sprint complete.

## Decisions that control scope

| Decision | Default | Change it when |
| --- | --- | --- |
| Geographic scope | Burnaby schools in the available public data | Another municipality has comparable fields and a clear user need. |
| Analytics | Preserve existing 100/250/500 m straight-line measures | Road-network or outcome data becomes available and its method can be validated. |
| Database | Versioned read-only exports for the first release | Refresh, multi-user writes, or query performance justifies PostGIS. |
| Accounts and editing | No authentication or public data edits | A defined user workflow requires saved work or controlled annotations. |
| Clusters | Optional explanatory view | Users understand the method and it adds value beyond count/distance comparisons. |

Potential later work: street-network distance, traffic-volume and collision datasets, neighbourhood matching, saved comparison sets, and an administrative refresh dashboard. Each needs a new data-quality and interpretation review. None is required to show a strong full-stack project.

## What to do next

1. Treat Sprint 1 as the next work item. Open with the product brief and wireframes, then commit the versioned export schema and a working school-detail API endpoint.
2. Use the included 3 August 2026 snapshot for initial development. Do not trigger a fresh City download until the staged refresh workflow exists.
3. In the first sprint review, compare actual effort against the 8–12 hour/week assumption, adjust remaining scope, and keep the Sprint 2 end-to-end demo as the highest priority.
