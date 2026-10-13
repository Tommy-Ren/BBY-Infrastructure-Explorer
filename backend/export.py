"""Export the committed report snapshot. Never downloads or edits report inputs.

Run from the repository root: python -m backend.export
"""

import argparse
import hashlib
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

from backend.models import Dataset, Infrastructure, Location

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "backend" / "data"
RADII = (100, 250, 500)
COVERAGE_RULE = (
    "All recorded traffic-calming features, including removed and unknown statuses. "
    "Nearest traffic signals exclude RMVD. These are historical records, not active-asset counts."
)
LIMITATION = (
    "Coverage is a straight-line distance from a school point, not walking distance "
    "or a measure of school safety, student exposure, or collisions."
)


def canonical(value):
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def text_or_none(value):
    return None if pd.isna(value) or not str(value).strip() else str(value).strip()


def match_school_ids(schools, registry):
    """Match reviewed name/location anchors, never mutable municipal OBJECTIDs."""
    anchors = registry["schools"]
    if len({s["id"] for s in anchors}) != len(anchors):
        raise ValueError("Duplicate application ID in school registry")
    matches = {}
    used = set()
    for school in schools.itertuples():
        candidates = [
            a
            for a in anchors
            if school.school_name in a["names"]
            and school.geometry.distance(Point(a["easting"], a["northing"])) <= 50
        ]
        if len(candidates) != 1 or candidates[0]["id"] in used:
            raise ValueError(f"School identity needs review: {school.school_name}")
        matches[school.school_id] = candidates[0]["id"]
        used.add(candidates[0]["id"])
    return matches


def read_layer(root, name, id_column):
    layer = gpd.read_file(root / "data" / "processed" / f"{name}.geojson")
    if layer.crs is None or layer.crs.to_epsg() != 26910:
        raise ValueError(f"{name}: expected EPSG:26910")
    if (
        layer.empty
        or layer[id_column].isna().any()
        or layer[id_column].duplicated().any()
        or layer.geometry.isna().any()
        or layer.geometry.is_empty.any()
        or (~layer.geometry.is_valid).any()
        or (layer.geometry.geom_type != "Point").any()
    ):
        raise ValueError(f"{name}: invalid IDs or point geometry")
    return layer


def read_table(root, name, schools):
    table = pd.read_csv(root / "output" / "tables" / name)
    if table.school_id.duplicated().any() or set(table.school_id) != set(
        schools.school_id
    ):
        raise ValueError(f"{name}: incomplete or duplicate school join")
    names = schools.set_index("school_id").school_name.to_dict()
    if any(names[r.school_id] != r.school_name for r in table.itertuples()):
        raise ValueError(f"{name}: school name mismatch")
    return table.set_index("school_id")


def build_dataset(root=ROOT):
    manifest = json.loads((root / "data/raw/manifest.json").read_text(encoding="utf-8"))
    # Verify the acquisition manifest before trusting the report provenance.
    for layer in manifest["layers"]:
        for kind in ("geojson", "metadata"):
            path = root / "data/raw" / layer[f"{kind}_file"]
            # Git may translate text line endings on checkout.
            if (
                digest(path.read_bytes().replace(b"\r\n", b"\n"))
                != layer[f"{kind}_sha256"]
            ):
                raise ValueError(f"Raw snapshot checksum mismatch: {path.name}")
    schools = read_layer(root, "schools", "school_id")
    calming = read_layer(root, "traffic_calming", "calming_id")
    signals = read_layer(root, "traffic_signals", "signal_id")
    intersections = read_layer(root, "intersections", "intersection_id")
    registry = json.loads(
        (root / "data/school_registry.json").read_text(encoding="utf-8")
    )
    if len(schools) != registry["expected_school_count"]:
        raise ValueError(
            "School count changed: review snapshot expectation and registry"
        )
    stable_ids = match_school_ids(schools, registry)
    features_table = read_table(root, "school_infrastructure_features.csv", schools)
    nearest_tables = {
        kind: read_table(root, f"school_nearest_{name}.csv", schools)
        for kind, name in [
            ("calming", "traffic_calming"),
            ("signal", "traffic_signals"),
            ("intersection", "intersections"),
        ]
    }
    infrastructure = {}
    layers = {
        "calming": (calming, "calming_id"),
        "signal": (signals, "signal_id"),
        "intersection": (intersections, "intersection_id"),
    }
    for kind, (layer, id_column) in layers.items():
        for row in layer.to_crs(4326).itertuples():
            source_id = int(getattr(row, id_column))
            description = (
                text_or_none(row.location)
                if kind == "calming"
                else text_or_none(row.unit_id)
                if kind == "signal"
                else " / ".join(
                    str(v)
                    for v in [row.street_name_1, row.street_name_2]
                    if not pd.isna(v)
                )
            )
            infrastructure[f"{kind}-{source_id}"] = Infrastructure(
                id=f"{kind}-{source_id}",
                source_id=source_id,
                type=row.calming_type if kind == "calming" else kind,
                location=Location(
                    longitude=round(row.geometry.x, 8),
                    latitude=round(row.geometry.y, 8),
                ),
                description=description,
                service_status=text_or_none(
                    getattr(row, "service_status", getattr(row, "status", None))
                ),
            ).model_dump()
    exported = []
    wgs_schools = schools.to_crs(4326).set_index("school_id")
    for school in schools.sort_values("school_name").itertuples():
        row = features_table.loc[school.school_id]
        point = wgs_schools.loc[school.school_id].geometry
        result = {
            "id": stable_ids[school.school_id],
            "source_id": int(school.school_id),
            "name": school.school_name,
            "dataset_version": "pending",
            "location": {"longitude": round(point.x, 8), "latitude": round(point.y, 8)},
            "counts": {},
            "radius_geometry": {},
        }
        for radius in RADII:
            count = int((calming.geometry.distance(school.geometry) <= radius).sum())
            if count != row[f"calming_count_{radius}m"]:
                raise ValueError(f"Coverage does not match CSV: {school.school_name}")
            result["counts"][f"radius_{radius}_m"] = count
            polygon = gpd.GeoSeries(
                [school.geometry.buffer(radius, quad_segs=32)], crs=26910
            ).to_crs(4326)[0]
            result["radius_geometry"][str(radius)] = {
                "type": "Polygon",
                "coordinates": [[[round(x, 8), round(y, 8)] for x, y in polygon.exterior.coords]],
            }
        for kind, (layer, id_column) in layers.items():
            eligible = (
                layer if kind != "signal" else layer[layer.service_status != "RMVD"]
            )
            distances = eligible.geometry.distance(school.geometry)
            nearest = nearest_tables[kind].loc[school.school_id]
            source_id = int(nearest[f"nearest_{kind}_id"])
            matched = eligible[eligible[id_column] == source_id]
            if len(matched) != 1:
                raise ValueError(f"Missing nearest {kind} join")
            measured = float(matched.geometry.distance(school.geometry).iloc[0])
            reported = float(row[f"nearest_{kind}_distance_m"])
            if (
                abs(measured - reported) > 0.001
                or abs(float(distances.min()) - measured) > 0.001
                or reported != float(nearest[f"nearest_{kind}_distance_m"])
            ):
                raise ValueError(
                    f"Nearest distance does not match CSV: {school.school_name}, {kind}"
                )
            result[f"nearest_{kind}"] = {
                "feature": infrastructure[f"{kind}-{source_id}"],
                "distance_m": reported,
            }
        exported.append(result)
    paths = [root / "data/raw/manifest.json", root / "data/school_registry.json"]
    paths += sorted((root / "data/processed").glob("*.geojson"))
    paths += [root / "data/processed/data_quality_summary.json"]
    paths += [
        root / "output/tables" / name
        for name in [
            "school_infrastructure_features.csv",
            "school_nearest_traffic_calming.csv",
            "school_nearest_traffic_signals.csv",
            "school_nearest_intersections.csv",
        ]
    ]
    metadata = {
        "schema_version": 1,
        "dataset_version": "pending",
        "retrieved_at_utc": manifest["retrieved_at_utc"],
        "radii_m": list(RADII),
        "school_count": len(exported),
        "feature_count": len(calming),
        "coverage_rule": COVERAGE_RULE,
        "limitation": LIMITATION,
        "sources": [
            {k: layer[k] for k in ("name", "source_url", "source_count")}
            for layer in manifest["layers"]
        ],
        "quality": json.loads(
            (root / "data/processed/data_quality_summary.json").read_text()
        ),
        "input_sha256": {
            str(p.relative_to(root)).replace("\\", "/"): digest(
                p.read_bytes().replace(b"\r\n", b"\n")
            )
            for p in paths
        },
    }
    data = Dataset(
        metadata=metadata,
        schools=exported,
        features=[infrastructure[f"calming-{i}"] for i in sorted(calming.calming_id)],
    ).model_dump()
    version = manifest["retrieved_at_utc"][:10] + "-" + digest(canonical(data))[:12]
    data["metadata"]["dataset_version"] = version
    for school in data["schools"]:
        school["dataset_version"] = version
    return Dataset.model_validate(data)


def write_export(output=DEFAULT_OUTPUT, root=ROOT):
    data = build_dataset(root)
    payload = canonical(data.model_dump())
    output.mkdir(parents=True, exist_ok=True)
    (output / "dataset.json").write_bytes(payload)
    (output / "manifest.json").write_bytes(
        canonical(
            {
                "schema_version": 1,
                "dataset_version": data.metadata.dataset_version,
                "file": "dataset.json",
                "sha256": digest(payload),
                "bytes": len(payload),
                "school_count": len(data.schools),
                "feature_count": len(data.features),
            }
        )
    )
    print(
        f"Exported {len(data.schools)} schools, {len(data.features)} features: {data.metadata.dataset_version}"
    )
    return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    write_export(parser.parse_args().output)
