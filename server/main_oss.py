from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path
import json
import re
from pydantic import BaseModel
from typing import Any, Dict
from datetime import datetime, timezone

app = FastAPI(
    title="IngressKit - Self-hosted data repair toolkit",
    description="Normalize messy CSVs, webhooks, and JSON data with deterministic, auditable transformations",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS for local development and self-hosted deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for your deployment
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Static files for documentation/landing page
base_dir = Path(__file__).parent
static_dir = base_dir / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir), html=False), name="static")


@app.get("/", response_class=HTMLResponse)
async def landing_page() -> HTMLResponse:
    """Landing page with IngressKit overview"""
    index = static_dir / "index.html"
    if index.exists():
        return HTMLResponse(index.read_text(encoding="utf-8"))
    
    # Fallback HTML if no static files
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>IngressKit - Self-hosted data repair toolkit</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; 
                   max-width: 800px; margin: 0 auto; padding: 2rem; line-height: 1.6; color: #333; }
            .header { text-align: center; margin-bottom: 3rem; }
            .tagline { color: #666; font-size: 1.2rem; margin-bottom: 2rem; }
            .oss-badge { background: #28a745; color: white; padding: 0.5rem 1rem; 
                        border-radius: 20px; font-size: 0.9rem; margin-bottom: 2rem; display: inline-block; }
            .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 2rem; margin-bottom: 3rem; }
            .feature { padding: 1.5rem; border: 1px solid #eee; border-radius: 8px; }
            .code { background: #f8f9fa; padding: 1rem; border-radius: 8px; font-family: 'Monaco', 'Consolas', monospace; 
                   border-left: 4px solid #007bff; margin: 2rem 0; }
            .cta-section { text-align: center; background: #f8f9fa; padding: 2rem; border-radius: 12px; margin: 3rem 0; }
            .cta-primary { background: #007bff; color: white; padding: 1rem 2rem; text-decoration: none; 
                          border-radius: 8px; font-weight: 600; margin: 0 1rem; display: inline-block; }
            .cta-secondary { background: #6c757d; color: white; padding: 1rem 2rem; text-decoration: none; 
                            border-radius: 8px; font-weight: 600; margin: 0 1rem; display: inline-block; }
            .support-section { background: #fff3cd; border: 1px solid #ffeaa7; padding: 1.5rem; border-radius: 8px; 
                              margin: 3rem 0; text-align: center; }
            .links { text-align: center; margin-top: 3rem; }
            .links a { margin: 0 1rem; color: #007bff; text-decoration: none; }
            .links a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🛠️ IngressKit</h1>
            <div class="oss-badge">✨ Free & Open Source</div>
            <p class="tagline">Self-hosted data repair toolkit.<br>Your data, your servers, no third-party risk.</p>
        </div>
        
        <div class="features">
            <div class="feature">
                <h3>🔧 CSV/Excel Repair</h3>
                <p>Smart header mapping, type coercion, unit conversion with complete audit trails.</p>
            </div>
            <div class="feature">
                <h3>🔗 Webhook Harmonization</h3>
                <p>Stripe, GitHub, Slack webhooks → unified canonical event format.</p>
            </div>
            <div class="feature">
                <h3>🧠 JSON Normalization</h3>
                <p>Fix LLM outputs and third-party JSON to strict schemas.</p>
            </div>
        </div>
        
        <div class="cta-section">
            <h2>🚀 Get Started in Seconds</h2>
            <p>IngressKit is completely free and MIT-licensed. No signup, no API keys, no limits.</p>
            <a href="https://github.com/pilothobs/ingresskit" class="cta-primary">Get IngressKit Free</a>
            <a href="/docs" class="cta-secondary">View API Docs</a>
        </div>
        
        <h2>Quick Start</h2>
        <div class="code">
# Install via pip
pip install ingresskit

# Or run with Docker
docker run -p 8080:8080 pilothobs/ingresskit

# Clean your first CSV
ingresskit repair --in messy.csv --out clean.csv --schema contacts
        </div>
        
        <div class="support-section">
            <h3>☕ Support Open Source Development</h3>
            <p>IngressKit is free and always will be. If this saves you time, consider supporting the project!</p>
            <a href="https://github.com/sponsors/pilothobs" style="color: #e91e63; font-weight: 600;">❤️ Become a Sponsor</a>
        </div>
        
        <div class="links">
            <a href="https://github.com/pilothobs/ingresskit">📚 GitHub</a>
            <a href="/docs">🔧 API Docs</a>
            <a href="https://github.com/pilothobs/ingresskit/blob/main/README.md">📖 Documentation</a>
            <a href="https://github.com/pilothobs/ingresskit/discussions">💬 Community</a>
        </div>
        
        <p style="text-align: center; margin-top: 3rem; color: #666; font-size: 0.9rem;">
            Built with ❤️ by <a href="https://github.com/pilothobs">@pilothobs</a> • 
            MIT Licensed • 
            <a href="https://github.com/pilothobs/ingresskit/blob/main/CONTRIBUTING.md">Contribute</a>
        </p>
    </body>
    </html>
    """
    return HTMLResponse(html_content)


@app.get("/ping")
@app.get("/v1/ping")
@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint for monitoring and load balancers"""
    return {"status": "healthy", "service": "ingresskit", "version": "0.1.0"}


# Data models for API requests/responses
class CanonicalEvent(BaseModel):
    """Unified event structure for all webhook sources"""
    event_id: str
    source: str
    occurred_at: str
    actor: Dict[str, Any] | None = None
    subject: Dict[str, Any] | None = None
    action: str
    metadata: Dict[str, Any] | None = None
    trace: list[Dict[str, Any]] | None = None


# Webhook normalization functions
def _utc_timestamp(ts: int | float | None) -> str:
    """Convert Unix timestamp to UTC ISO format"""
    if ts is None:
        return datetime.now(timezone.utc).isoformat()
    try:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()


def normalize_stripe_webhook(payload: Dict[str, Any]) -> CanonicalEvent:
    """Convert Stripe webhook to canonical event format"""
    obj = payload.get("data", {}).get("object", {})
    trace = [{"op": "stripe_normalize", "timestamp": datetime.now(timezone.utc).isoformat()}]
    
    return CanonicalEvent(
        event_id=str(payload.get("id", "")),
        source="stripe",
        occurred_at=_utc_timestamp(payload.get("created")),
        actor={"id": obj.get("customer")} if obj.get("customer") else None,
        subject={
            "type": obj.get("object", "unknown"),
            "id": obj.get("id")
        },
        action=str(payload.get("type", "unknown")),
        metadata={k: v for k, v in obj.items() if k not in {"id", "object", "customer"}},
        trace=trace
    )


def normalize_github_webhook(payload: Dict[str, Any]) -> CanonicalEvent:
    """Convert GitHub webhook to canonical event format"""
    action = payload.get("action", "unknown")
    issue = payload.get("issue") or payload.get("pull_request") or {}
    sender = payload.get("sender") or {}
    
    trace = [{"op": "github_normalize", "timestamp": datetime.now(timezone.utc).isoformat()}]
    
    return CanonicalEvent(
        event_id=str(payload.get("id", "")),
        source="github",
        occurred_at=datetime.now(timezone.utc).isoformat(),
        actor={
            "id": sender.get("id"),
            "login": sender.get("login")
        } if sender else None,
        subject={
            "type": "issue" if "issue" in payload else "pull_request" if "pull_request" in payload else "unknown",
            "id": issue.get("id"),
            "number": issue.get("number")
        },
        action=action,
        metadata={
            "title": issue.get("title"),
            "url": issue.get("html_url"),
            "repository": payload.get("repository", {}).get("full_name")
        },
        trace=trace
    )


def normalize_slack_webhook(payload: Dict[str, Any]) -> CanonicalEvent:
    """Convert Slack webhook to canonical event format"""
    event = payload.get("event", {})
    trace = [{"op": "slack_normalize", "timestamp": datetime.now(timezone.utc).isoformat()}]
    
    return CanonicalEvent(
        event_id=str(payload.get("event_id", "")),
        source="slack",
        occurred_at=_utc_timestamp(payload.get("event_time")),
        actor={"id": event.get("user")} if event.get("user") else None,
        subject={
            "type": event.get("type", "message"),
            "channel": event.get("channel")
        },
        action=event.get("type", "message"),
        metadata={k: v for k, v in event.items() if k not in {"user", "channel", "type"}},
        trace=trace
    )


@app.post("/v1/webhooks/normalize", response_model=CanonicalEvent)
async def normalize_webhook(request: Request, source: str):
    """
    Normalize webhooks from various sources into canonical event format
    
    Supported sources:
    - stripe: Stripe payment webhooks
    - github: GitHub repository webhooks  
    - slack: Slack workspace webhooks
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Route to appropriate normalizer
    if source == "stripe":
        return normalize_stripe_webhook(payload)
    elif source == "github":
        return normalize_github_webhook(payload)
    elif source == "slack":
        return normalize_slack_webhook(payload)
    else:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported webhook source: {source}. Supported: stripe, github, slack"
        )


def normalize_contact_json(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize contact data to canonical schema"""
    # Extract and clean email
    email = (
        data.get("email") or 
        data.get("Email") or 
        data.get("e-mail") or 
        data.get("mail") or 
        ""
    ).strip().lower()
    
    # Extract and clean phone (digits only)
    phone_raw = (
        data.get("phone") or 
        data.get("Phone") or 
        data.get("telephone") or 
        data.get("tel") or 
        ""
    ).strip()
    phone = re.sub(r"\D", "", phone_raw) if phone_raw else None
    
    # Extract and parse name
    name = (
        data.get("name") or 
        data.get("Name") or 
        data.get("full_name") or 
        ""
    ).strip()
    
    first_name, last_name = "", ""
    if "," in name:
        # "Last, First" format
        parts = [x.strip() for x in name.split(",", 1)]
        last_name, first_name = parts[0], parts[1] if len(parts) > 1 else ""
    elif " " in name:
        # "First Last" format  
        parts = name.split(" ", 1)
        first_name, last_name = parts[0], parts[1] if len(parts) > 1 else ""
    else:
        first_name = name
    
    # Extract company
    company = (
        data.get("company") or 
        data.get("Company") or 
        data.get("organization") or 
        data.get("org") or 
        None
    )
    
    trace = [
        {"op": "normalize_contact", "timestamp": datetime.now(timezone.utc).isoformat()},
        {"op": "email_lowercase", "field": "email"} if email else None,
        {"op": "phone_digits_only", "field": "phone"} if phone else None,
        {"op": "parse_name", "field": "name"} if name else None,
    ]
    trace = [t for t in trace if t is not None]
    
    return {
        "email": email or None,
        "phone": phone or None,
        "first_name": first_name or None,
        "last_name": last_name or None,
        "company": company,
        "trace": trace
    }


@app.post("/v1/json/normalize")
async def normalize_json(request: Request, schema: str):
    """
    Normalize JSON data according to predefined schemas
    
    Supported schemas:
    - contacts: Normalize contact/customer data
    """
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    if schema == "contacts":
        return normalize_contact_json(data)
    else:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported schema: {schema}. Supported: contacts"
        )


@app.get("/v1/schemas")
async def list_schemas():
    """List available schemas for JSON normalization"""
    return {
        "schemas": {
            "contacts": {
                "description": "Normalize contact/customer data",
                "fields": ["email", "phone", "first_name", "last_name", "company"],
                "example_input": {
                    "Email": "USER@EXAMPLE.COM",
                    "Name": "Doe, Jane", 
                    "Phone": "(555) 123-4567"
                },
                "example_output": {
                    "email": "user@example.com",
                    "phone": "5551234567",
                    "first_name": "Jane",
                    "last_name": "Doe",
                    "company": None
                }
            }
        },
        "webhook_sources": ["stripe", "github", "slack"]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
