# Official data refresh

The app checks the City's four ArcGIS layers every six hours through `.github/workflows/refresh-data.yml`, at 00:23, 06:23, 12:23, and 18:23 UTC. GitHub may delay scheduled jobs, so this is a check cadence, not a real-time freshness guarantee. Run the workflow manually from Actions to refresh immediately. It does not depend on a developer's computer being on.

Each run downloads paginated official records with bounded retries, checks unique IDs and final source membership, cleans in EPSG:26910, recomputes distances and radius counts, validates CSV joins and school identities, and verifies checksums and the API contract. Acquisition is staged outside the published directory. Unexpected identities, missing geometry, or record counts falling more than 20% or increasing more than 50% stop publication for review. Ordinary feature additions and attribute changes publish automatically.

After Python, frontend build, and browser tests pass, the workflow commits only `backend/data/dataset.json` and `backend/data/manifest.json` to `main`. A concurrent branch update rejects the push rather than overwriting it. The existing Vercel Git integration then deploys `main`; the workflow polls the public metadata endpoint for the exact new dataset version and fails if it has not appeared within ten minutes. Bot pushes do not automatically run another GitHub Actions workflow, so the refresh workflow performs all checks itself.

GitHub's built-in job token needs `contents: write` to commit the validated export. No additional repository secrets or Vercel account token are required. The existing Vercel Git integration deploys both normal code pushes and the data commits from `github-actions[bot]`; this was verified with the first hosted refresh.

## What users see

The header shows **Last synced from City data**, with the successful acquisition time in UTC and the six-hour check cadence. This is distinct from the City's own edit date, which these sources do not consistently provide. A successful check can advance this time without changing record contents. The content fingerprint makes that distinction auditable. After 24 hours without a successful published download, a warning points users to the official sources. Previously opened browser tabs need a reload to fetch the new deployment's data.

If acquisition, validation, or tests fail, the prior validated deployment remains available. GitHub marks the refresh run failed; repository notification preferences control notifications. If deployment fails after a validated data commit, the production site retains its previous release and the workflow fails its version check. Inspect Actions and Vercel logs, resolve the cause, and rerun the workflow. Scheduled runs resume automatically. Public-repository schedules may be disabled by GitHub after prolonged repository inactivity; check Actions if the displayed sync becomes stale.

## Audit and recovery

- Successful runs retain complete raw acquisition manifests, downloaded layers, cleaned layers, calculated tables, and the export as an Actions artifact for 14 days. Git history retains published application snapshots.
- The original August report data and results remain untouched. Existing historical regression tests continue to validate their fixed values. Current API and browser checks read expected values from the active export/API, so normal municipal changes do not break the UI tests.
- For a school rename, move, opening, or retirement, inspect official records and review `data/school_registry.json` before retrying. Preserve previously allocated IDs; do not regenerate the registry or relax its checks to force a deployment.
- To reproduce locally: `python -m backend.refresh --archive tmp/refresh-audit`, then run the checks in `DEVELOPMENT.md`. This contacts the City and changes only the application export and the requested audit directory.
- To roll back: restore both application data files from a known-good Git commit and deploy that commit. If the cause remains unresolved, disable the refresh workflow in Actions until it is repaired; re-enable it afterward.

The first refresh on 13 October 2026 retrieved 64 schools and 1,500 traffic-calming records, up from 1,494 in the August report. Status inclusion and straight-line measurement rules are unchanged.
