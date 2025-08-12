## IngressKit

Make anything fit. Files, webhooks, and AI outputs normalized.

### What is it?
- CSV/Excel Import Repair SDK (Python first): cleans, maps, and validates messy files into a canonical schema with an audit trace.
- Webhook Harmonizer (hosted-ready FastAPI): turns Stripe/GitHub/Slack webhooks into one predictable event format.
- JSON Normalizer: repairs LLM or third-party JSON to a strict schema.

### Why it exists
- Every app ingests data. Most teams reimplement CSV importers and webhook parsers repeatedly. IngressKit provides a lightweight, deterministic alternative with per-tenant memory so it gets better over time.

### Components
- sdk/python: Repairer library + CLI to fix CSV/Excel files.
- server: Minimal FastAPI app with endpoints for webhooks and JSON normalization.
- docs: Quickstart and API snippets.
- examples: Sample files and scripts to try locally.

### Quickstart (local)
1) Python SDK
```
cd sdk/python
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m ingresskit.cli --in ../../examples/contacts_messy.csv --out ../../examples/contacts_clean.csv --schema contacts
```

2) Server (Webhook Harmonizer + JSON Normalizer)
```
cd server
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

Test endpoints:
```
curl -X POST "http://localhost:8080/v1/webhooks/ingest?source=stripe" -H "Content-Type: application/json" -d '{"id":"evt_1","type":"charge.succeeded","data":{"object":{"id":"ch_1","amount":1234,"customer":"cus_1"}},"created":1723380000}' | jq .

curl -X POST "http://localhost:8080/v1/json/normalize?schema=contacts" -H "Content-Type: application/json" -d '{"Email":"USER@EXAMPLE.COM","Phone":"(555) 123-4567","Name":" Doe, Jane "}' | jq .
```

### Notes
- Starter scaffold to begin integration quickly. Expand schemas, rules, and providers as you go.


