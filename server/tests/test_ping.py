from fastapi.testclient import TestClient
from main import app


client = TestClient(app)


def test_ping_v1():
    r = client.get("/v1/ping")
    assert r.status_code == 200
    assert r.json() == {"message": "pong"}


def test_ping_root():
    r = client.get("/ping")
    assert r.status_code == 200
    assert r.json() == {"message": "pong"}


