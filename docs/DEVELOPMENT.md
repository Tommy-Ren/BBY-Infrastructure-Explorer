# Local development and verification

Prerequisites: Python 3.11 and Node.js 22.12 or newer within the 22.x release line. Run commands from the repository root unless specified. Do not run `download_data.py` to develop this app.

## Setup (PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-dev.lock
.venv\Scripts\python.exe -m backend.export --output tmp/report-export
.venv\Scripts\python.exe -m pytest -q
npm --prefix frontend ci
npm --prefix frontend run build
```

On macOS/Linux, replace `.venv\Scripts\python.exe` with `.venv/bin/python`. This export verifies the historical report inputs without overwriting current application data. Reproducing the entire report pipeline remains optional and is documented in the original README section below.

To download official data and update the application export, run `.venv\Scripts\python.exe -m backend.refresh --archive tmp/refresh-audit`. See [refresh operations](DATA_REFRESH.md) for validation, deployment, and recovery. Do not overwrite the historical `data/raw`, `data/processed`, or `output` directories.

Start the API:

```powershell
.venv\Scripts\python.exe -m uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
npm --prefix frontend run dev
```

Open http://127.0.0.1:5173 and API docs at http://127.0.0.1:8000/docs. The Vite development server proxies `/api` to port 8000. The frontend's `VITE_API_BASE_URL` defaults to empty (same origin). If hosting separately, set it before building and set the backend's `CORS_ORIGINS` to the exact allowed frontend origins, comma-separated. Backend variables are process environment variables; the example `.env` is documentation and is not loaded automatically.

## Browser checks

```powershell
cd frontend
npx playwright install chromium
npm run test:e2e
```

Playwright starts both servers if they are not already running. Tests use the actual exported API dataset and exercise desktop and Pixel 7-sized layouts. Failure cases deliberately interrupt API calls and map tiles. CI runs Python tests, confirms regeneration produces no dataset diff, type-checks/builds the frontend, and runs Chromium browser checks. CI is configured in `.github/workflows/checks.yml`; a local test result is not evidence of a GitHub-hosted run.

The API runtime only needs `backend/requirements.txt` plus `backend/data/`; GeoPandas and report libraries are needed to export/validate the data, not to serve requests.

## Two-minute demonstration

1. Search “Alpha” and select Alpha Secondary.
2. Confirm 24 recorded features at 250 m and nearest calming distance 95.1 m.
3. Switch to 100 m (1 feature), then 500 m (93 features); inspect the radius and points.
4. Copy the link and reload: selection and radius persist. Browser back/forward restores prior selections.
5. Search an unmatched name and clear it; inspect the inline coverage limitation and source date.
6. Scroll to the methodology and City source links. Repeat on a narrow viewport.
