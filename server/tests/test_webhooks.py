import json
from pathlib import Path
from fastapi.testclient import TestClient

from main import app


FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def load_fixture(name: str) -> dict:
    with (FIXTURES / name).open("r", encoding="utf-8") as f:
        return json.load(f)


client = TestClient(app)


def test_stripe_charge_succeeded():
    payload = load_fixture("stripe_charge_succeeded.json")
    resp = client.post("/v1/webhooks/ingest?source=stripe", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["source"] == "stripe"
    assert data["action"] == "charge.succeeded"
    assert data["subject"]["type"] == "charge"
    assert data["actor"]["id"] == "cus_1"


def test_github_issue_opened():
    payload = load_fixture("github_issue_opened.json")
    resp = client.post("/v1/webhooks/ingest?source=github", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["source"] == "github"
    assert data["action"] == "opened"
    assert data["subject"]["type"] == "issue"
    assert data["metadata"]["title"] == "Bug: crash on launch"


def test_slack_message():
    payload = load_fixture("slack_message.json")
    resp = client.post("/v1/webhooks/ingest?source=slack", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["source"] == "slack"
    assert data["action"] == "message"
    assert data["subject"]["type"] == "message"

