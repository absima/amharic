from fastapi.testclient import TestClient

from api.app import app

client = TestClient(app)


def test_resolve_ui_api_login_alias():
    r = client.post("/resolve-ui", json={"text": "ygbu"})
    assert r.status_code == 200
    out = r.json()
    assert out["resolved"] is True
    assert out["key"] == "ui.auth.login"
    assert out["am"] == "ይግቡ"


def test_resolve_ui_api_unresolved():
    r = client.post("/resolve-ui", json={"text": "___nope___"})
    assert r.status_code == 200
    out = r.json()
    assert out["resolved"] is False
