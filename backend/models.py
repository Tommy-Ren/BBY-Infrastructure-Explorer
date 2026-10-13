"""Version 1 public data contract. Coordinates are always longitude, latitude."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

NonNegative = Annotated[float, Field(ge=0, allow_inf_nan=False)]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Location(Contract):
    longitude: Annotated[float, Field(ge=-123.1, le=-122.8, allow_inf_nan=False)]
    latitude: Annotated[float, Field(ge=49.1, le=49.35, allow_inf_nan=False)]


class Infrastructure(Contract):
    id: str
    source_id: int
    type: str
    location: Location
    description: str | None = None
    service_status: str | None = None


class NearestFeature(Contract):
    feature: Infrastructure
    distance_m: NonNegative


class Counts(Contract):
    radius_100_m: Annotated[int, Field(ge=0)]
    radius_250_m: Annotated[int, Field(ge=0)]
    radius_500_m: Annotated[int, Field(ge=0)]

    @model_validator(mode="after")
    def monotone(self):
        if not self.radius_100_m <= self.radius_250_m <= self.radius_500_m:
            raise ValueError("Radius counts must be monotone")
        return self


class SchoolSummary(Contract):
    id: str
    source_id: int
    name: str
    location: Location


class School(SchoolSummary):
    dataset_version: str
    counts: Counts
    nearest_calming: NearestFeature
    nearest_signal: NearestFeature
    nearest_intersection: NearestFeature
    # These polygons are constructed in EPSG:26910 before conversion to WGS84.
    radius_geometry: dict[str, dict]


class Source(Contract):
    name: str
    source_url: str
    source_count: int


class DatasetMetadata(Contract):
    schema_version: Literal[1] = 1
    dataset_version: str
    retrieved_at_utc: str
    coordinate_crs: Literal["EPSG:4326"] = "EPSG:4326"
    measurement_crs: Literal["EPSG:26910"] = "EPSG:26910"
    distance_unit: Literal["m"] = "m"
    radii_m: list[int]
    school_count: int
    feature_count: int
    coverage_rule: str
    limitation: str
    sources: list[Source]
    quality: dict
    input_sha256: dict[str, str]


class Dataset(Contract):
    metadata: DatasetMetadata
    schools: list[School]
    features: list[Infrastructure]

    @model_validator(mode="after")
    def consistency(self):
        for rows, expected in [
            (self.schools, self.metadata.school_count),
            (self.features, self.metadata.feature_count),
        ]:
            if len(rows) != expected or len({r.id for r in rows}) != len(rows):
                raise ValueError("Dataset row count or unique ID validation failed")
        if any(
            s.dataset_version != self.metadata.dataset_version for s in self.schools
        ):
            raise ValueError("School version does not match dataset")
        return self


class SchoolPage(Contract):
    items: list[SchoolSummary]
    total: int
    limit: int
    offset: int
    dataset_version: str


class FeaturePage(Contract):
    items: list[Infrastructure]
    total: int
    limit: int
    offset: int
    dataset_version: str
