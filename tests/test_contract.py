import copy
import hashlib
import json
import shutil

import geopandas as gpd
import pandas as pd
import pytest
from pydantic import ValidationError
from pyproj import Transformer
from shapely.geometry import Point

from backend.app import load_dataset
from backend.export import ROOT, build_dataset, canonical, match_school_ids, read_table
from backend.models import Counts, NearestFeature
from clean_layers import clean_schools
from analyse_distances import nearest_traffic_calming, nearest_traffic_signals
from analyse_summaries import count_nearby_traffic_calming


def test_export_matches_committed_snapshot_and_all_csv_rows(exported):
    assert len(exported.schools) == 64
    assert len(exported.features) == 1494
    assert len({s.id for s in exported.schools}) == 64
    rows = pd.read_csv(
        ROOT / "output/tables/school_infrastructure_features.csv"
    ).set_index("school_id")
    for school in exported.schools:
        row = rows.loc[school.source_id]
        assert school.name == row.school_name
        for radius in [100, 250, 500]:
            assert (
                getattr(school.counts, f"radius_{radius}_m")
                == row[f"calming_count_{radius}m"]
            )
        for kind in ["calming", "signal", "intersection"]:
            assert (
                getattr(school, f"nearest_{kind}").distance_m
                == row[f"nearest_{kind}_distance_m"]
            )
    assert (
        canonical(exported.model_dump())
        == (ROOT / "backend/data/dataset.json").read_bytes()
    )


def test_export_is_deterministic(exported):
    assert canonical(exported.model_dump()) == canonical(build_dataset().model_dump())


def test_geographic_conversion_and_radius_polygons(exported):
    projected = gpd.read_file(ROOT / "data/processed/schools.geojson").set_index(
        "school_id"
    )
    to_metres = Transformer.from_crs(4326, 26910, always_xy=True)
    for school in exported.schools:
        x, y = to_metres.transform(school.location.longitude, school.location.latitude)
        assert Point(x, y).distance(projected.loc[school.source_id].geometry) < 0.01
        for radius in [100, 250, 500]:
            for lon, lat in school.radius_geometry[str(radius)]["coordinates"][0]:
                bx, by = to_metres.transform(lon, lat)
                assert abs(Point(bx, by).distance(Point(x, y)) - radius) < 0.01


def test_status_rule_including_unknown_and_removed_calming():
    schools = gpd.GeoDataFrame(
        {"school_id": [1], "school_name": ["Example"]},
        geometry=[Point(500000, 5450000)],
        crs=26910,
    )
    calming = gpd.GeoDataFrame(
        {
            "calming_id": [1, 2, 3, 4],
            "calming_type": ["Speed Hump"] * 4,
            "service_status": ["RMVD", "I", None, " "],
        },
        geometry=[Point(500000 + d, 5450000) for d in [10, 20, 30, 100]],
        crs=26910,
    )
    assert (
        count_nearby_traffic_calming(schools, calming).iloc[0].calming_count_100m == 4
    )
    assert nearest_traffic_calming(schools, calming).iloc[0].nearest_calming_id == 1
    signals = (
        calming.iloc[:2]
        .rename(columns={"calming_id": "signal_id"})
        .assign(unit_id=["removed", "retained"])
    )
    assert nearest_traffic_signals(schools, signals).iloc[0].nearest_signal_id == 2


def test_registry_survives_source_id_reassignment_and_requires_review():
    schools = gpd.read_file(ROOT / "data/processed/schools.geojson")
    registry = json.loads((ROOT / "data/school_registry.json").read_text())
    original = list(match_school_ids(schools, registry).values())
    schools.school_id += 1000
    assert list(match_school_ids(schools, registry).values()) == original
    renamed = schools.copy()
    renamed.loc[0, "school_name"] = "Unreviewed rename"
    with pytest.raises(ValueError, match="needs review"):
        match_school_ids(renamed, registry)
    schools.loc[0, "geometry"] = Point(0, 0)
    with pytest.raises(ValueError, match="needs review"):
        match_school_ids(schools, registry)
    bad_registry = copy.deepcopy(registry)
    bad_registry["schools"][1]["id"] = bad_registry["schools"][0]["id"]
    with pytest.raises(ValueError, match="Duplicate"):
        match_school_ids(schools, bad_registry)


def test_school_count_is_a_configurable_review_gate():
    places = gpd.GeoDataFrame(
        {"OBJECTID": [1], "DESCRIPTION": ["School"], "PLACETYPE": [500]},
        geometry=[Point(-122.96, 49.25)],
        crs=4326,
    )
    with pytest.raises(RuntimeError, match="Review the snapshot"):
        clean_schools(places)
    assert len(clean_schools(places, expected_school_count=1)) == 1
    duplicate = pd.concat([places, places], ignore_index=True)
    with pytest.raises(RuntimeError, match="IDs"):
        clean_schools(duplicate, expected_school_count=2)


@pytest.mark.parametrize("counts", [(-1, 2, 3), (2, 1, 3), (1, 3, 2)])
def test_bad_counts_are_rejected(counts):
    with pytest.raises(ValidationError):
        Counts(radius_100_m=counts[0], radius_250_m=counts[1], radius_500_m=counts[2])


@pytest.mark.parametrize("distance", [-1, float("nan"), float("inf")])
def test_invalid_distance_rejected(distance, exported):
    with pytest.raises(ValidationError):
        NearestFeature(feature=exported.features[0], distance_m=distance)


def test_missing_or_duplicate_joins_rejected(tmp_path):
    output = tmp_path / "output/tables"
    output.mkdir(parents=True)
    schools = gpd.read_file(ROOT / "data/processed/schools.geojson")
    table = pd.read_csv(ROOT / "output/tables/school_infrastructure_features.csv")
    for changed in [table.iloc[1:], pd.concat([table, table.iloc[:1]])]:
        changed.to_csv(output / "test.csv", index=False)
        with pytest.raises(ValueError, match="join"):
            read_table(tmp_path, "test.csv", schools)


def test_checksum_failure_blocks_api_startup(tmp_path):
    shutil.copy(ROOT / "backend/data/manifest.json", tmp_path / "manifest.json")
    (tmp_path / "dataset.json").write_text("{}")
    with pytest.raises(ValueError, match="checksum"):
        load_dataset(tmp_path)
    manifest = json.loads((ROOT / "backend/data/manifest.json").read_text())
    assert (
        manifest["sha256"]
        == hashlib.sha256((ROOT / "backend/data/dataset.json").read_bytes()).hexdigest()
    )
