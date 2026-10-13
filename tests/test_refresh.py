from datetime import datetime, timezone
import shutil

import pytest

from backend.app import load_dataset
from backend.export import DEFAULT_OUTPUT
from backend.refresh import refresh, validate_change


def candidate():
    data = load_dataset(DEFAULT_OUTPUT).model_copy(deep=True)
    data.metadata.retrieved_at_utc = datetime.now(timezone.utc).isoformat()
    return data


def test_refresh_accepts_small_source_updates():
    previous = candidate()
    updated = previous.model_copy(deep=True)
    updated.metadata.sources[1].source_count += 6
    validate_change(previous, updated)


@pytest.mark.parametrize("change", ["missing_school", "mass_deletion", "mass_addition", "old_download"])
def test_refresh_rejects_suspicious_changes(change):
    previous = candidate()
    updated = previous.model_copy(deep=True)
    if change == "missing_school":
        updated.schools.pop()
    elif change == "mass_deletion":
        updated.metadata.sources[1].source_count = 1
    elif change == "mass_addition":
        updated.metadata.sources[1].source_count *= 3
    else:
        updated.metadata.retrieved_at_utc = "2020-01-01T00:00:00+00:00"
    with pytest.raises(ValueError):
        validate_change(previous, updated)


def test_failed_refresh_leaves_published_bytes_unchanged(tmp_path, monkeypatch):
    output = tmp_path / "data"
    shutil.copytree(DEFAULT_OUTPUT, output)
    before = {p.name: p.read_bytes() for p in output.iterdir()}

    def fail(*args):
        raise RuntimeError("Incomplete municipal download")

    monkeypatch.setattr("backend.refresh.build_candidate", fail)
    with pytest.raises(RuntimeError, match="Incomplete"):
        refresh(output)
    assert before == {p.name: p.read_bytes() for p in output.iterdir()}


def test_downloader_rejects_membership_changes(tmp_path, monkeypatch):
    from download_arcgis import download_layer
    responses = iter([
        {"fields": [{"name": "OBJECTID", "type": "esriFieldTypeOID"}]},
        {"count": 1},
        {"type": "FeatureCollection", "features": [{"properties": {"OBJECTID": 1}, "geometry": {"type": "Point", "coordinates": [0, 0]}}]},
        {"objectIds": [2]},
    ])
    monkeypatch.setattr("download_arcgis.request_json", lambda *args: next(responses))
    with pytest.raises(RuntimeError, match="changed during download"):
        download_layer(None, "test", "https://example.test/layer", tmp_path)
    assert not list(tmp_path.iterdir())
