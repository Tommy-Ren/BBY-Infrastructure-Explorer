import pytest


def test_health_metadata_and_openapi(client):
    assert client.get("/health").json()["status"] == "ok"
    metadata = client.get("/api/v1/datasets/current").json()
    assert metadata["school_count"] == 64
    assert metadata["coordinate_crs"] == "EPSG:4326"
    assert metadata["retrieved_at_utc"].startswith("2026-08-03")
    assert "/api/v1/schools/{school_id}" in client.get("/openapi.json").json()["paths"]


def test_search_pagination_and_detail(client):
    page = client.get(
        "/api/v1/schools", params={"search": " ALPHA ", "limit": 1}
    ).json()
    assert page["total"] == 1
    school = client.get("/api/v1/schools/" + page["items"][0]["id"]).json()
    assert school["name"] == "Alpha Secondary"
    assert school["source_id"] == 69
    assert school["counts"] == {
        "radius_100_m": 1,
        "radius_250_m": 24,
        "radius_500_m": 93,
    }
    assert school["nearest_calming"]["distance_m"] == 95.125
    assert client.get("/api/v1/schools?search=nonexistent").json()["items"] == []
    assert client.get("/api/v1/schools?offset=64").json()["items"] == []
    assert client.get("/api/v1/schools/not-a-school").status_code == 404
    first = client.get("/api/v1/schools?limit=1").json()["items"]
    second = client.get("/api/v1/schools?limit=1&offset=1").json()["items"]
    assert first[0]["id"] != second[0]["id"]


@pytest.mark.parametrize(
    "query",
    [
        "limit=0",
        "limit=101",
        "offset=-1",
        "limit=nope",
        "offset=10001",
        "search=" + "a" * 101,
    ],
)
def test_bad_school_queries(client, query):
    response = client.get("/api/v1/schools?" + query)
    assert response.status_code == 422
    assert "detail" in response.json()


@pytest.mark.parametrize(
    "query",
    [
        "",
        "bbox=bad",
        "bbox=NaN,49,-122.9,49.1",
        "bbox=-123,49,-122,50",
        "bbox=-123,49,-123,49.01",
        "bbox=-122.9,49,-123,49.01",
        "bbox=-123,49,-122.99,49.01&limit=501",
        "bbox=-123,49,-122.99,49.01&offset=-1",
    ],
)
def test_bounded_feature_queries(client, query):
    assert client.get("/api/v1/features?" + query).status_code == 422


def test_feature_filter_and_pagination(client):
    bbox = "-122.999,49.27,-122.989,49.29"
    page = client.get("/api/v1/features", params={"bbox": bbox, "limit": 1}).json()
    assert page["total"] > 1 and len(page["items"]) == 1
    row = page["items"][0]
    assert -122.999 <= row["location"]["longitude"] <= -122.989
    second = client.get(
        "/api/v1/features", params={"bbox": bbox, "limit": 1, "offset": 1}
    ).json()
    assert second["items"][0]["id"] != row["id"]
    assert (
        client.get(
            "/api/v1/features", params={"bbox": bbox, "type": "nonexistent"}
        ).json()["total"]
        == 0
    )


def test_cors_is_restricted_and_api_read_only(client):
    assert (
        client.get("/health", headers={"Origin": "http://localhost:5173"}).headers[
            "access-control-allow-origin"
        ]
        == "http://localhost:5173"
    )
    assert (
        "access-control-allow-origin"
        not in client.get(
            "/health", headers={"Origin": "https://untrusted.example"}
        ).headers
    )
    assert client.post("/api/v1/schools").status_code == 405
