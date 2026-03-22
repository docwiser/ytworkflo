"""
ytworkflo — Test Suite
Uses httpx AsyncClient against the FastAPI app (no real YT calls).
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["platform"] == "ytworkflo"


def test_openapi_schema():
    r = client.get("/openapi.json")
    assert r.status_code == 200
    schema = r.json()
    assert schema["info"]["title"] == "ytworkflo"
    assert "paths" in schema


def test_docs_available():
    r = client.get("/docs")
    assert r.status_code == 200


def test_redoc_available():
    r = client.get("/redoc")
    assert r.status_code == 200


def test_root_redirects():
    r = client.get("/", follow_redirects=False)
    assert r.status_code in (302, 307)


def test_search_get_missing_query():
    r = client.get("/api/v1/search")
    assert r.status_code == 422


def test_suggest_endpoint_exists():
    # No real network in test, just ensure route is registered
    r = client.get("/api/v1/search/suggest?q=python")
    # Will either return 200 (with results) or 200 (empty list on network fail)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_openapi_has_all_tags():
    r = client.get("/openapi.json")
    schema = r.json()
    tags_in_schema = {t["name"] for t in schema.get("tags", [])}
    all_paths_tags = set()
    for path_data in schema["paths"].values():
        for method_data in path_data.values():
            for tag in method_data.get("tags", []):
                all_paths_tags.add(tag)
    expected_tags = {
        "Search", "Video", "Channel", "Playlist", "Download",
        "Stream", "Audio", "Transcript", "Thumbnails", "Analytics",
        "Batch", "Formats", "Comments", "Trending", "Subtitles", "System"
    }
    for tag in expected_tags:
        assert tag in all_paths_tags, f"Tag '{tag}' missing from API paths"


def test_trending_regions_endpoint():
    r = client.get("/api/v1/trending/regions")
    assert r.status_code == 200
    data = r.json()
    assert "regions" in data
    assert len(data["regions"]) > 0


def test_trending_categories_endpoint():
    r = client.get("/api/v1/trending/categories")
    assert r.status_code == 200
    data = r.json()
    assert "categories" in data


def test_download_list_endpoint():
    r = client.get("/api/v1/download/list")
    assert r.status_code == 200
    data = r.json()
    assert "files" in data
    assert "total" in data


def test_formats_filter_missing_body():
    r = client.post("/api/v1/formats/filter", json={})
    assert r.status_code == 422


def test_batch_videos_empty_list():
    r = client.post("/api/v1/batch/videos", json={"video_ids": []})
    assert r.status_code == 422  # min_length=1 enforced


def test_search_post_missing_query():
    r = client.post("/api/v1/search", json={})
    assert r.status_code == 422
