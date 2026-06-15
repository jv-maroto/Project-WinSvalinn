"""Smoke tests for the Tauri sidecar (FastAPI)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


def test_sidecar_imports():
    from sidecar.app import app

    assert app is not None
    assert app.title == "WinSvalinn Sidecar"


def test_sidecar_has_expected_endpoints():
    from sidecar.app import app

    paths = {r.path for r in app.routes if hasattr(r, "path")}
    expected = {
        "/health",
        "/system/health",
        "/system/info",
        "/security/audit",
        "/security/ports",
        "/security/processes",
        "/optimization/score",
        "/optimization/{action}",
        "/memory/stats",
        "/memory/free",
        "/processes/tree",
        "/network/connections",
        "/cleanup/analyze",
        "/cleanup/clean",
        "/config",
    }
    missing = expected - paths
    assert not missing, f"missing endpoints: {missing}"


def test_health_endpoint_via_test_client():
    from fastapi.testclient import TestClient

    from sidecar.app import app

    with TestClient(app) as client:
        r = client.get("/health")
        assert r.status_code == 200
        body = r.json()
        assert body["ok"] is True
        assert "version" in body


def test_system_info_endpoint_returns_real_data():
    from fastapi.testclient import TestClient

    from sidecar.app import app

    with TestClient(app) as client:
        r = client.get("/system/info")
        assert r.status_code == 200
        body = r.json()
        assert "os" in body
        assert "python" in body


def test_system_health_endpoint_returns_score():
    from fastapi.testclient import TestClient

    from sidecar.app import app

    with TestClient(app) as client:
        r = client.get("/system/health")
        assert r.status_code == 200
        body = r.json()
        assert "score" in body and isinstance(body["score"], int)
        assert 0 <= body["score"] <= 100
        assert "cpu" in body and "ram" in body and "disk" in body


def test_plugins_endpoint_removed():
    """The legacy plugin system was replaced by the native options registry."""
    from sidecar.app import app

    paths = {r.path for r in app.routes if hasattr(r, "path")}
    assert not any(p.startswith("/plugins") for p in paths)


def test_options_endpoint_lists_options():
    from fastapi.testclient import TestClient

    from sidecar.app import app

    with TestClient(app) as client:
        r = client.get("/options")
        assert r.status_code == 200
        body = r.json()
        assert "options" in body
        assert isinstance(body["options"], list)
        assert len(body["options"]) > 0
