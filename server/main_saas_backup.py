from fastapi import FastAPI, Request, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path
import os
from dotenv import load_dotenv
import json
import stripe
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

# Static splash page
base_dir = Path(__file__).parent
static_dir = base_dir / "static"
app.mount("/static", StaticFiles(directory=str(static_dir), html=False), name="static")


@app.get("/", response_class=HTMLResponse)
async def splash() -> HTMLResponse:
    index = static_dir / "index.html"
    if index.exists():
        return HTMLResponse(index.read_text(encoding="utf-8"), headers={"Cache-Control": "no-store"})
    return HTMLResponse("<h1>IngressKit</h1><p>Lightweight data ingress toolkit.</p>", headers={"Cache-Control": "no-store"})


# Simple health check
@app.get("/v1/ping")
@app.get("/ping")
async def ping() -> dict[str, str]:
    return {"message": "pong"}


# --- Simple API key + credit meter (starter) ---
"""Load env from server/.env, then fallback to project root .env if present"""
load_dotenv(base_dir / ".env", override=True)
load_dotenv(base_dir.parent / ".env", override=True)

# --- Simple persistent keystore (JSON) ---
data_dir = base_dir / "data"
data_dir.mkdir(exist_ok=True)
balances_file = data_dir / "balances.json"


class KeyStore:
    def __init__(self, path: Path):
        self.path = path
        if not self.path.exists():
            self._write({})

    def _read(self) -> dict:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _write(self, data: dict) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def get_balance(self, key: str) -> int:
        return int(self._read().get(key, 0))

    def set_balance(self, key: str, value: int) -> None:
        data = self._read()
        data[key] = int(value)
        self._write(data)

    def add_credits(self, key: str, delta: int) -> int:
        bal = self.get_balance(key) + int(delta)
        self.set_balance(key, bal)
        return bal

    def charge(self, key: str, delta: int = 1) -> int:
        bal = self.get_balance(key)
        if bal <= 0:
            raise HTTPException(status_code=402, detail="Out of credits")
        bal -= int(delta)
        self.set_balance(key, bal)
        return bal


KEYS = KeyStore(balances_file)

# Seed from env if provided (e.g., "key1:25000,key2:5000")
seed = os.getenv("INGRESSKIT_API_KEYS")
if seed:
    for pair in seed.split(','):
        if ':' in pair:
            k, v = pair.split(':', 1)
            k = k.strip()
            try:
                KEYS.add_credits(k, int(v))
            except Exception:
                pass

FREE_CREDITS_PER_DAY = int(os.getenv("INGRESSKIT_FREE_PER_DAY") or 100)


def require_api_key(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing API key")
    key = authorization.split(" ", 1)[1]
    return key


def charge_credit(key: str) -> None:
    # Known key: charge persistent balance. Unknown key: allow (free tier placeholder)
    if KEYS.get_balance(key) > 0:
        KEYS.charge(key, 1)
    else:
        return


# --- Stripe Checkout + Webhook (auto-credit) ---
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
ADMIN_TOKEN = os.getenv("INGRESSKIT_ADMIN_TOKEN", "")
PRICE_MAP = {}
price_map_env = os.getenv("INGRESSKIT_PRICE_MAP")  # e.g., price_123:5000,price_456:20000
if price_map_env:
    for pair in price_map_env.split(','):
        if ':' in pair:
            p, c = pair.split(':', 1)
            try:
                PRICE_MAP[p.strip()] = int(c)
            except Exception:
                pass

# Optional alias mapping for frontend plan names → Stripe price IDs
ALIASES: dict[str, str] = {}
aliases_env = os.getenv("INGRESSKIT_PRICE_ALIASES")  # e.g., price_small:price_live_123,price_med:price_live_456
if aliases_env:
    for pair in aliases_env.split(','):
        if ':' in pair:
            a, pid = pair.split(':', 1)
            ALIASES[a.strip()] = pid.strip()


class CheckoutRequest(BaseModel):
    price_id: str
    api_key: str
    mode: str | None = None  # 'payment' or 'subscription'
    success_url: str | None = None
    cancel_url: str | None = None


@app.post("/v1/billing/create_checkout")
async def create_checkout(req: CheckoutRequest):
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    success = req.success_url or os.getenv("CHECKOUT_SUCCESS_URL") or "https://ingresskit.com/"
    cancel = req.cancel_url or os.getenv("CHECKOUT_CANCEL_URL") or "https://ingresskit.com/"
    try:
        price_id = req.price_id
        # Map alias first if present; otherwise accept direct Stripe price ID
        if price_id in ALIASES:
            price_id = ALIASES[price_id]
        checkout_mode = req.mode or "payment"
        session = stripe.checkout.Session.create(
            mode=checkout_mode,
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=cancel,
            metadata={"api_key": req.api_key},
        )
        return {"url": session.get("url")}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"stripe_error:{type(e).__name__}:{str(e)}")


@app.post("/v1/billing/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    try:
        event = stripe.Webhook.construct_event(payload, sig, secret) if secret else json.loads(payload)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid_signature")

    if event.get("type") == "checkout.session.completed":
        session = event.get("data", {}).get("object", {})
        api_key = (session.get("metadata") or {}).get("api_key")
        if api_key:
            # Determine credits from line items via price map
            credits_total = 0
            line_items = []
            try:
                line_items = stripe.checkout.Session.list_line_items(session.get("id"), limit=10).get("data", [])
            except Exception:
                pass
            for li in line_items:
                price_id = ((li.get("price") or {}).get("id")) or ""
                credits_total += PRICE_MAP.get(price_id, 0)
            if credits_total > 0:
                KEYS.add_credits(api_key, credits_total)
    return {"received": True}


@app.get("/v1/billing/balance")
async def get_balance(api_key: str = Depends(require_api_key)):
    balance = KEYS.get_balance(api_key)
    return {"api_key": api_key, "balance": balance}


class AdminCreditRequest(BaseModel):
    api_key: str
    amount: int


@app.post("/v1/admin/credit")
async def admin_credit(req: AdminCreditRequest, x_admin_token: str | None = Header(default=None)):
    if not ADMIN_TOKEN or x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="unauthorized")
    new_bal = KEYS.add_credits(req.api_key, req.amount)
    return {"api_key": req.api_key, "balance": new_bal}


@app.get("/v1/billing/resolve")
async def resolve_price(name: str):
    resolved = ALIASES.get(name, name)
    return {"input": name, "resolved": resolved, "aliases": ALIASES}


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
async def ingest(request: Request, source: str, api_key: str = Depends(require_api_key)):
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

    charge_credit(api_key)
    return ev.model_dump()


@app.post("/v1/json/normalize")
async def json_normalize(request: Request, schema: str, api_key: str = Depends(require_api_key)):
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
        charge_credit(api_key)
        return out

    raise HTTPException(status_code=400, detail="Unsupported schema")


def re_digits(v: str) -> str | None:
    if not v:
        return None
    import re

    d = re.sub(r"\D", "", v)
    return d or None


