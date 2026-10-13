"""Download and validate official data in staging before replacing the app export.

The August report inputs stay unchanged. Run: python -m backend.refresh
"""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from backend.app import load_dataset
from backend.export import ROOT, DEFAULT_OUTPUT, write_export

REFRESH_HOURS = 6


def validate_change(previous, candidate):
    """Require review for identity changes or unusually large source changes."""
    if {s.id for s in candidate.schools} != {s.id for s in previous.schools}:
        raise ValueError("School identities changed; review the school registry")
    old_counts = {s.name: s.source_count for s in previous.metadata.sources}
    for source in candidate.metadata.sources:
        old = old_counts.get(source.name)
        if old and not 0.8 <= source.source_count / old <= 1.5:
            raise ValueError(f"Unusual record count change in {source.name}; review before publishing")
    stamp = datetime.fromisoformat(candidate.metadata.retrieved_at_utc)
    if stamp.tzinfo is None or abs((datetime.now(timezone.utc) - stamp).total_seconds()) > 86400:
        raise ValueError("Refresh acquisition timestamp is not current")


def build_candidate(work, output):
    raw = work / "data/raw"
    processed = work / "data/processed"
    registry = json.loads((ROOT / "data/school_registry.json").read_text())
    shutil.copyfile(ROOT / "data/school_registry.json", work / "data/school_registry.json")
    subprocess.run([sys.executable, str(ROOT / "src/download_data.py"), str(raw)], check=True)
    acquisition = json.loads((raw / "manifest.json").read_text())
    if any(layer["missing_geometry_count"] for layer in acquisition["layers"]):
        raise ValueError("Source contains missing geometry; review before publishing")
    subprocess.run([
        sys.executable, str(ROOT / "src/clean_data.py"), str(raw), str(processed),
        "--expected-school-count", str(registry["expected_school_count"]),
    ], check=True)
    subprocess.run([
        sys.executable, str(ROOT / "src/analyse_coverage.py"), str(processed),
        str(work / "output/tables"),
    ], check=True)
    # Normalize staging paths so provenance does not depend on the machine.
    acquisition["output_directory"] = "data/raw"
    (raw / "manifest.json").write_text(json.dumps(acquisition, indent=2) + "\n", encoding="utf-8", newline="\n")
    candidate = write_export(work / "export", work, refresh_interval_hours=REFRESH_HOURS)
    validate_change(load_dataset(output), candidate)
    load_dataset(work / "export")  # Exercise the same integrity checks as API startup.
    return candidate


def refresh(output=DEFAULT_OUTPUT, archive=None):
    output = Path(output)
    # A failed download, cleaner, export, or validation never touches published files.
    with tempfile.TemporaryDirectory(prefix="burnaby-refresh-") as temporary:
        work = Path(temporary)
        (work / "data").mkdir()
        candidate = build_candidate(work, output)
        if archive:
            shutil.copytree(work, archive, dirs_exist_ok=True)
        for name in ("dataset.json", "manifest.json"):
            staged = output / (name + ".tmp")
            shutil.copyfile(work / "export" / name, staged)
            staged.replace(output / name)
        print(f"Validated official data: {candidate.metadata.dataset_version}")
        return candidate


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--archive", type=Path, help="Keep acquired sources and intermediate tables for audit")
    args = parser.parse_args()
    refresh(args.output, args.archive)
