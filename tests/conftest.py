import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from backend.app import create_app
from backend.export import build_dataset


@pytest.fixture(scope="session")
def exported():
    return build_dataset()


@pytest.fixture
def client():
    with TestClient(create_app()) as client:
        yield client
