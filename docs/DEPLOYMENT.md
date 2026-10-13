# Vercel preview deployment

Verified preview: https://bby-infrastructure-explorer-eg5c1zl6f.vercel.app

The public homepage, API, OpenAPI docs, school selection, radius changes, map selection, and shared-link reload were verified against this deployment on desktop and mobile on 13 October 2026. This new demo project's Vercel Authentication setting is disabled so the link works without a Vercel account. No paid plan change was made.

The user selected Vercel for Sprint 2. The root `vercel.json` defines a Vite frontend and a FastAPI backend using [Vercel Services](https://vercel.com/docs/services). Both share one public origin: `/api/*`, `/health`, `/docs`, `/redoc`, and `/openapi.json` route to FastAPI; remaining requests route to Vite. This avoids per-preview CORS wildcards. The config uses the current `services` key, not the older `experimentalServices` model.

Services is currently beta and available across plans. Confirm the account's applicable [pricing and limits](https://vercel.com/docs/services/pricing) before a durable deployment; these can change. This project has no database, accounts, secrets, or background refresh jobs.

## Deploy from the repository root

1. Follow `docs/DEVELOPMENT.md` and pass the local checks. Commit the generated `backend/data/` export alongside its code and tests.
2. Run `npx vercel login` in your terminal if not already authenticated. Keep credentials in Vercel's login flow, never in source files.
3. Run `npx vercel deploy`. Use the repository root as the project root so both services and the root routing configuration are included. Do not select only `frontend/` as the root.
4. Leave `VITE_API_BASE_URL` unset/empty. Same-origin routing works for every preview URL. `CORS_ORIGINS` is only needed for explicitly separate origins.
5. Verify the preview root, `/health`, `/docs`, `/api/v1/datasets/current`, and a selected-school link. Confirm the snapshot version agrees across API responses.
6. Test from a signed-out browser. If Vercel deployment protection is enabled, configure the preview's access deliberately before calling it a public portfolio demo.

The API's `app:app` entrypoint runs with `backend/` as its service root. It verifies and loads the committed export during startup. There is no geospatial computation or source download during the serverless request path. Python 3.12 is specified in `backend/.python-version`; Vercel's build image does not provide Python 3.11. The offline report/export workflow remains tested on Python 3.11. The API needs no geospatial libraries and serves the same validated JSON on both versions.

For an optional local container run from the repository root:

```sh
docker build -f backend/Dockerfile -t burnaby-explorer-api .
docker run --rm -p 8000:8000 burnaby-explorer-api
```

The image serves the API only. Vercel uses its native FastAPI runtime, so Docker is not a prerequisite for the preview.

## External resources and limitations

Vercel Web Analytics is enabled for this project. The frontend mounts
`@vercel/analytics/react` once at the application root; Vercel supplies its
analytics script and collection endpoint on deployed pages. Local development
uses the package's development mode. No custom events are configured.

The browser loads OpenStreetMap raster tiles with visible attribution and Google Fonts with system-font fallbacks. No offline tile prefetch is implemented. Map data has a list/text alternative, and a failed map does not block school details. The lazy-loaded MapLibre bundle is substantial; keep this visible as a performance follow-up rather than hiding the build warning.

A working local app and deployment configuration do not constitute a public preview. Record the actual URL and external smoke-test result in `docs/SPRINT_REVIEW_1_2.md` after deployment.
