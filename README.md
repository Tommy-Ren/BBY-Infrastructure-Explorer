# Burnaby School Area Traffic-Calming Coverage

## Infrastructure Explorer application

**[Open the live app](https://bby-infrastructure-explorer.vercel.app)** ·
[API documentation](https://bby-infrastructure-explorer.vercel.app/docs)

The app checks official Burnaby data every six hours and publishes validated updates automatically. The header shows the last successful sync; a warning appears after 24 hours without one. [Refresh and recovery details](docs/DATA_REFRESH.md). The August research dataset below remains preserved for reproducibility.

The repository now includes a React/TypeScript map and a read-only FastAPI API
for regularly refreshed official data. The first 13 October 2026 refresh includes
**64 schools and 1,500 recorded traffic-calming features**. Search, select a school, switch 100/250/500 m radii,
inspect nearest distances and sources, and share the selected-school URL.
Recorded coverage is straight-line proximity, not a measure of school safety.

- [Local setup, checks, and demo](docs/DEVELOPMENT.md)
- [Data contract and status/identity decisions](docs/DATA_CONTRACT.md)
- [Product brief and desktop/mobile wireframes](docs/PRODUCT_BRIEF.md)
- [Vercel deployment](docs/DEPLOYMENT.md)
- [Sprint 1–2 review and outstanding release gates](docs/SPRINT_REVIEW_1_2.md)

Application code lives in `backend/` and `frontend/`; automated checks live in
`tests/` and `frontend/e2e/`. The original analysis below remains reproducible.

This project provides a reproducible geospatial analysis of traffic-calming
coverage around schools in Burnaby, BC.

## Requirements

The project was tested with Python 3.11.9. Dependencies are listed in `requirements.txt`:

| Package | Main use |
| --- | --- |
| `requests` | ArcGIS REST downloads |
| `pandas` | Tabular cleaning and summaries |
| `geopandas` | Projection, spatial joins, and distances |
| `scipy` | Statistical tests |
| `matplotlib` | Maps and statistical figures |
| `scikit-learn` | Standardization, PCA, K-means, and silhouette scores |

Create a virtual environment from the project root:

```bash
python -m venv .venv
```

On Windows PowerShell, activate it and install the dependencies with:

```powershell
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Reproduce the report outputs

The repository includes the raw ArcGIS snapshot used for the report. To
reproduce the published results exactly, run these commands from the project
root without downloading new data:

```bash
python src/clean_data.py
python src/analyse_coverage.py
python src/create_plots.py
python src/cluster_schools.py
python src/create_cluster_plot.py
```

The commands run in this order:

| Step | Default input | Default output |
| --- | --- | --- |
| `clean_data.py` | `data/raw/` | `data/processed/` |
| `analyse_coverage.py` | `data/processed/` | `output/tables/` |
| `create_plots.py` | Processed layers and result tables | Four core SVG figures |
| `cluster_schools.py` | `school_infrastructure_features.csv` | Diagnostics, PCA, and cluster CSV files |
| `create_cluster_plot.py` | Processed layers and clustering tables | PCA cluster plot and cluster map |

All output directories are created when needed. Existing files with the same
names are replaced.

## Download a current data snapshot

To retrieve the current City of Burnaby records before running the remaining
pipeline, use:

```bash
python src/download_data.py
```

This replaces the files in `data/raw/` with a new API snapshot. The City can
reassign internal `OBJECTID` values over time, so a new download may not be
byte-for-byte identical to the report snapshot even when the infrastructure
locations and analysis results are unchanged. The generated
`data/raw/manifest.json` records source counts, retrieval time, spatial
references, filenames, and SHA-256 checksums.

## Custom input and output paths

Commands also support explicit paths:

```text
python src/download_data.py [output_directory]
python src/clean_data.py [input_directory output_directory]
python src/analyse_coverage.py [input_directory output_directory]
python src/create_plots.py [spatial_directory table_directory output_directory]
python src/cluster_schools.py [input_file output_directory]
python src/create_cluster_plot.py [spatial_directory table_directory output_directory]
```

## Project outputs

- `data/raw/` contains the downloaded GeoJSON, ArcGIS metadata, and manifest.
- `data/processed/` contains cleaned GeoJSON in EPSG:26910 and a data-quality
  summary.
- `output/tables/` contains school distances, coverage summaries, statistical
  tests, PCA diagnostics, and cluster assignments and profiles.
- `output/figures/` contains the six SVG figures used for analysis and
  reporting.

## Repository structure

```text
CMPT-353-Project/
├── README.md
├── report.pdf
├── requirements.txt
├── data/
│   ├── raw/                  # Report data snapshot and metadata
│   └── processed/            # Cleaned projected layers
├── output/
│   ├── tables/               # Generated CSV results
│   └── figures/              # Generated SVG figures
└── src/
    ├── download_*.py         # ArcGIS acquisition and validation
    ├── clean_*.py            # Layer cleaning and quality checks
    ├── analyse_*.py          # Spatial summaries and statistical tests
    ├── cluster_*.py          # Feature diagnostics, PCA, and K-means
    ├── plot_*.py             # Figure input and drawing functions
    ├── create_plots.py       # Core figure command
    └── create_cluster_plot.py # Cluster figure command
```
