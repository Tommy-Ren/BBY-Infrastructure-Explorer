"""Read-only API; no geospatial dependencies or municipal requests at runtime."""

from contextlib import asynccontextmanager
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

if __package__:
    from .models import (
        Dataset,
        DatasetMetadata,
        FeaturePage,
        School,
        SchoolPage,
        SchoolSummary,
    )
else:  # Vercel imports app:app with backend/ as the service root.
    from models import (
        Dataset,
        DatasetMetadata,
        FeaturePage,
        School,
        SchoolPage,
        SchoolSummary,
    )

DATA_DIRECTORY = Path(__file__).resolve().parent / "data"


def load_dataset(directory):
    raw = (directory / "dataset.json").read_bytes()
    manifest = json.loads((directory / "manifest.json").read_text())
    if hashlib.sha256(raw).hexdigest() != manifest["sha256"]:
        raise ValueError("Application dataset checksum mismatch; regenerate the export")
    dataset = Dataset.model_validate_json(raw)
    if dataset.metadata.dataset_version != manifest["dataset_version"]:
        raise ValueError("Application dataset version mismatch")
    return dataset


def create_app(directory=DATA_DIRECTORY):
    @asynccontextmanager
    async def lifespan(app):
        app.state.dataset = load_dataset(Path(directory))
        app.state.schools = {s.id: s for s in app.state.dataset.schools}
        yield

    app = FastAPI(
        title="Burnaby School Infrastructure Explorer",
        version="1.0.0",
        lifespan=lifespan,
    )
    origins = [
        s.strip()
        for s in os.getenv(
            "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
        ).split(",")
        if s.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["GET"],
        allow_headers=["Accept"],
    )

    @app.get("/health")
    def health():
        return {
            "status": "ok",
            "dataset_version": app.state.dataset.metadata.dataset_version,
        }

    @app.get("/api/v1/datasets/current", response_model=DatasetMetadata)
    def current_dataset():
        return app.state.dataset.metadata

    @app.get("/api/v1/schools", response_model=SchoolPage)
    def schools(
        search: Annotated[str, Query(max_length=100)] = "",
        limit: Annotated[int, Query(ge=1, le=100)] = 100,
        offset: Annotated[int, Query(ge=0, le=10000)] = 0,
    ):
        selected = [
            s
            for s in app.state.dataset.schools
            if search.strip().casefold() in s.name.casefold()
        ]
        return SchoolPage(
            items=[
                SchoolSummary(**s.model_dump(include=set(SchoolSummary.model_fields)))
                for s in selected[offset : offset + limit]
            ],
            total=len(selected),
            limit=limit,
            offset=offset,
            dataset_version=app.state.dataset.metadata.dataset_version,
        )

    @app.get("/api/v1/schools/{school_id}", response_model=School)
    def school(school_id: str):
        if school_id not in app.state.schools:
            raise HTTPException(
                status_code=404, detail="School not found in this dataset"
            )
        return app.state.schools[school_id]

    @app.get("/api/v1/features", response_model=FeaturePage)
    def features(
        bbox: Annotated[
            str,
            Query(
                max_length=120,
                description="west,south,east,north in EPSG:4326; maximum span 0.1 degrees",
            ),
        ],
        type: Annotated[str | None, Query(max_length=80)] = None,
        limit: Annotated[int, Query(ge=1, le=500)] = 500,
        offset: Annotated[int, Query(ge=0, le=10000)] = 0,
    ):
        try:
            west, south, east, north = map(float, bbox.split(","))
            if not (
                all(math.isfinite(v) for v in (west, south, east, north))
                and -180 <= west < east <= 180
                and -90 <= south < north <= 90
                and east - west <= 0.1
                and north - south <= 0.1
            ):
                raise ValueError()
        except ValueError:
            raise HTTPException(
                422,
                detail="bbox must be west,south,east,north with positive spans <= 0.1 degrees",
            )
        selected = [
            f
            for f in app.state.dataset.features
            if west <= f.location.longitude <= east
            and south <= f.location.latitude <= north
            and (type is None or f.type == type)
        ]
        return FeaturePage(
            items=selected[offset : offset + limit],
            total=len(selected),
            limit=limit,
            offset=offset,
            dataset_version=app.state.dataset.metadata.dataset_version,
        )

    return app


app = create_app()
