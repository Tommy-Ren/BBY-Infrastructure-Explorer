# Application data contract v1

## Provenance

The application uses the committed snapshot retrieved at **2026-08-03T22:09:29.409201+00:00**, without a new municipal download. The authoritative acquisition manifest is `data/raw/manifest.json`, including SHA-256 hashes of each raw GeoJSON and metadata file.

| Layer | Records | Source |
| --- | ---: | --- |
| Places of Interest | 135; 64 schools selected by `PLACETYPE=500` | https://gis.burnaby.ca/arcgis/rest/services/OpenData/OpenData1/MapServer/1 |
| Traffic calming | 1,494 | https://gis.burnaby.ca/arcgis/rest/services/OpenData/OpenData5/MapServer/3 |
| Traffic signals | 269 | https://gis.burnaby.ca/arcgis/rest/services/OpenData/OpenData5/MapServer/1 |
| Intersections | 3,229 | https://gis.burnaby.ca/arcgis/rest/services/OpenData/OpenData5/MapServer/5 |

The cleaned layers in `data/processed/` use EPSG:26910. Source `OBJECTID` becomes `school_id`, `calming_id`, `signal_id`, or `intersection_id` in these layers. `DESCRIPTION` becomes `school_name`; `TYPE` is decoded to `calming_type` using the downloaded metadata; `SERVSTAT` becomes `service_status`. The quality summary records missing values, geometry issues, undocumented types, and placeholder dates.

## Service-status decision

The snapshot's calming records have 1,168 `I`, 11 `RMVD`, 308 null, and 7 whitespace status values. The downloaded `SERVSTAT` metadata has no coded-value domain. We retain **every recorded calming feature**, including removed and unknown statuses, for counts and nearest-calming distance. This matches the report. We do not infer that `I` guarantees an active asset. Labels say **recorded features**, never active infrastructure.

The signal metric retains the report's separate rule: exclude `RMVD` (1 of 269 records). The UI explicitly says “Excludes removed signals.” Intersections are not status-filtered. Regression tests put a removed calming feature nearest a synthetic school and a removed signal nearer than a retained one; the calming feature must count and the removed signal must not be chosen. A point at exactly the radius is included.

## Measurement and missing values

- Distances are planar Euclidean metres from the City's school **point** to feature points in EPSG:26910. Counts use `distance <= radius` at 100, 250, and 500 m.
- Export recomputes all counts and nearest distances from projected geometry, validates every CSV join, and retains the CSV distances rounded to three decimal places. The UI displays one decimal place and `m` units.
- Map locations are converted to EPSG:4326 with longitude first. Export validates a Burnaby-area envelope and round-trip tests check projected coordinates to within 1 cm.
- Displayed radius polygons are buffered in EPSG:26910 before conversion, using 32 segments per quadrant. Exported coordinates are rounded to eight decimal places (sub-centimetre precision) to avoid insignificant platform-dependent floating-point differences. They are visual approximations of the circular boundary; counts use direct distances, not polygon membership.
- Missing or blank optional feature descriptions/statuses become JSON `null`. Unknown type codes retain the cleaning pipeline's “Unlabelled code …”; missing types retain “Missing.” Missing school identities, geometries, nearest joins, or distances fail validation instead of becoming zero.
- Negative, infinite, and NaN distances are rejected. Counts must be nonnegative integers and monotone across radii. No statistical cluster is exposed in this version.

## Stable school identity and count review

`data/school_registry.json` owns opaque `sch-…` identifiers, a list of reviewed name aliases, and projected coordinate anchors. The initial IDs were assigned once and committed; **never regenerate this registry from a fresh snapshot**. Municipal `OBJECTID` is retained only as `source_id`.

For another snapshot, exact reviewed name plus a location within 50 m must identify exactly one registry entry; each entry can match only once. A reassigned source ID does not change the application ID. A rename, larger relocation, ambiguous match, or new school fails export and needs a human review of source records. Add a name alias or update an anchor only after review; new schools receive a new opaque ID. Retired IDs remain reserved and must not be reused. This initial matching gate is implemented; a staged refresh/change-report workflow belongs to Sprint 4.

The registry's `expected_school_count` is the app snapshot expectation. A mismatch stops export with a review message. The report cleaner defaults to its 64-school expectation but accepts an explicit reviewed count with `--expected-school-count`; valid IDs and names remain required. A different count is not itself evidence of corrupt data, and changing an expectation is a reviewed snapshot change.

## Export and integrity

`python -m backend.export` writes `backend/data/dataset.json` and a sidecar `manifest.json`. The JSON contains `metadata`, `schools`, and `features` (calming only). Nearest signal/intersection records are embedded in school details. The manifest records schema version, dataset version, byte count, school/feature counts, and the SHA-256 hash of the complete dataset file. API startup verifies its hash before accepting the dataset.

The version is the retrieval date plus 12 characters of a SHA-256 hash over canonical exported content with version placeholders. Canonical JSON sorts keys, uses compact UTF-8 serialization, and forbids non-finite values. Input checksums cover the source manifest, registry, cleaned layers, quality summary, and joined CSVs. Source text is normalized to LF for provenance hashes across Git checkouts; the application dataset checksum covers exact bytes. `.gitattributes` preserves LF for dataset files. No wall-clock generation time enters the hash.

## HTTP contract

Interactive OpenAPI: `/docs`; machine-readable schema: `/openapi.json`. All endpoints are GET-only and return JSON.

| Route | Contract |
| --- | --- |
| `/health` | Loaded dataset status and version |
| `/api/v1/datasets/current` | Schema/version, retrieval timestamp, CRS, metres, radii, source URLs/counts, status rule, limitations, quality, input hashes |
| `/api/v1/schools?search=&limit=&offset=` | Case-insensitive substring search, alphabetic snapshot order, total and page; limit 1–100, default 100; offset 0–10000; search ≤100 characters |
| `/api/v1/schools/{id}` | Stable/source IDs, name, WGS84 location, dataset version, `counts.radius_100_m/radius_250_m/radius_500_m`, nearest calming/signal/intersection records with `distance_m`, radius polygons |
| `/api/v1/features?bbox=&type=&limit=&offset=` | Required WGS84 `west,south,east,north`; finite ordered coordinates; each span ≤0.1 degrees; exact optional type filter; limit 1–500, default 500; offset 0–10000 |

Pagination includes `items`, `total`, `limit`, `offset`, and `dataset_version`. Geometry uses named `longitude`/`latitude` fields except GeoJSON radius polygons, which use `[longitude, latitude]`. Feature identifiers such as `calming-1044` are scoped to this snapshot; only school IDs promise cross-snapshot stability. A feature's `source_id`, `type`, optional `description`, optional `service_status`, and location are exposed.

Unknown school: HTTP 404. Invalid input: HTTP 422. Errors consistently have a top-level `detail` field (a message for domain validation, FastAPI's structured list for parameter validation). Requests are bounded; the frontend pages viewport results and clears stale points before loading another viewport.
