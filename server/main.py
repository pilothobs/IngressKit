from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict
from datetime import datetime, timezone

app = FastAPI(title="IngressKit Server", version="0.1.0")

# CORS for docs or demo origins (adjust as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.ingresskit.com",
        "https://ingresskit.com",
        "https://ingresskit.dev",
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CanonicalEvent(BaseModel):
    event_id: str
    source: str
    occurred_at: str
    actor: Dict[str, Any] | None = None
    subject: Dict[str, Any] | None = None
    action: str
    metadata: Dict[str, Any] | None = None
    trace: list[Dict[str, Any]] | None = None


def _utc_ts(ts: int | float | None) -> str:
    if ts is None:
        return datetime.now(timezone.utc).isoformat()
    try:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()


def normalize_stripe(payload: Dict[str, Any]) -> CanonicalEvent:
    obj = payload.get("data", {}).get("object", {})
    trace = []
    ev = CanonicalEvent(
        event_id=str(payload.get("id")),
        source="stripe",
        occurred_at=_utc_ts(payload.get("created")),
        actor={"id": obj.get("customer")},
        subject={"type": obj.get("object", "unknown"), "id": obj.get("id")},
        action=str(payload.get("type", "unknown")),
        metadata={k: v for k, v in obj.items() if k not in {"id", "object", "customer"}},
        trace=trace,
    )
    trace.append({"op": "map", "field": "amount", "from": "amount", "to": "amount"})
    return ev


def normalize_github(payload: Dict[str, Any]) -> CanonicalEvent:
    action = payload.get("action", "unknown")
    issue = payload.get("issue") or {}
    sender = payload.get("sender") or {}
    ev = CanonicalEvent(
        event_id=str(payload.get("id", "")),
        source="github",
        occurred_at=datetime.now(timezone.utc).isoformat(),
        actor={"id": sender.get("id"), "login": sender.get("login")},
        subject={"type": "issue", "id": issue.get("id"), "number": issue.get("number")},
        action=action,
        metadata={"title": issue.get("title"), "url": issue.get("html_url")},
        trace=[{"op": "map", "field": "title", "from": "issue.title", "to": "metadata.title"}],
    )
    return ev


def normalize_slack(payload: Dict[str, Any]) -> CanonicalEvent:
    ev = payload.get("event", {})
    return CanonicalEvent(
        event_id=str(payload.get("event_id", "")),
        source="slack",
        occurred_at=_utc_ts(payload.get("event_time")),
        actor={"id": ev.get("user")},
        subject={"type": ev.get("type", "message"), "channel": ev.get("channel")},
        action=ev.get("type", "message"),
        metadata={k: v for k, v in ev.items() if k not in {"user", "channel", "type"}},
        trace=[{"op": "map", "field": "text", "from": "event.text", "to": "metadata.text"}],
    )


@app.post("/v1/webhooks/ingest")
async def ingest(request: Request, source: str):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    if source == "stripe":
        ev = normalize_stripe(payload)
    elif source == "github":
        ev = normalize_github(payload)
    elif source == "slack":
        ev = normalize_slack(payload)
    else:
        raise HTTPException(status_code=400, detail="Unsupported source")

    return ev.model_dump()


@app.post("/v1/json/normalize")
async def json_normalize(request: Request, schema: str):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Minimal repair example for contacts schema
    if schema == "contacts":
        email = (data.get("email") or data.get("Email") or "").strip().lower()
        phone = (data.get("phone") or data.get("Phone") or "").strip()
        name = (data.get("name") or data.get("Name") or "").strip()
        first, last = "", ""
        if "," in name:
            last, first = [x.strip() for x in name.split(",", 1)]
        elif " " in name:
            first, last = name.split(" ", 1)
        out = {
            "email": email or None,
            "phone": re_digits(phone),
            "first_name": first or None,
            "last_name": last or None,
            "company": None,
            "trace": [
                {"op": "lower", "field": "email"},
                {"op": "digits", "field": "phone"},
                {"op": "split_name", "field": "name"},
            ],
        }
        return out

    raise HTTPException(status_code=400, detail="Unsupported schema")


def re_digits(v: str) -> str | None:
    if not v:
        return None
    import re

    d = re.sub(r"\D", "", v)
    return d or None


