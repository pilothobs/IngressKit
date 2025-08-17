# IngressKit Quick API Reference

## Quick Start

### Server Setup
```bash
cd server
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8080
```

### SDK Usage
```bash
cd sdk/python  
pip install -r requirements.txt
python -m ingresskit.cli --in messy.csv --out clean.csv --schema contacts
```

## API Endpoints Quick Reference

### Core Endpoints

| Method | Endpoint | Purpose | Auth Required |
|--------|----------|---------|---------------|
| `GET` | `/ping` | Health check | No |
| `GET` | `/` | Landing page | No |
| `POST` | `/v1/webhooks/ingest` | Process webhooks | Yes |
| `POST` | `/v1/json/normalize` | Normalize JSON | Yes |

### Billing Endpoints

| Method | Endpoint | Purpose | Auth Required |
|--------|----------|---------|---------------|
| `GET` | `/v1/billing/balance` | Check credits | API Key |
| `POST` | `/v1/billing/create_checkout` | Create payment | No |
| `POST` | `/v1/billing/webhook` | Stripe webhooks | Signature |
| `GET` | `/v1/billing/resolve` | Resolve price aliases | No |

### Admin Endpoints

| Method | Endpoint | Purpose | Auth Required |
|--------|----------|---------|---------------|
| `POST` | `/v1/admin/credit` | Add credits | Admin Token |

## Authentication

```bash
# API Key (Bearer Token)
Authorization: Bearer your-api-key

# Admin Token (Header)
X-Admin-Token: your-admin-token
```

## Webhook Processing

### Supported Sources
- `stripe` - Stripe payment webhooks
- `github` - GitHub repository webhooks  
- `slack` - Slack workspace webhooks

### Usage
```bash
curl -X POST "http://localhost:8080/v1/webhooks/ingest?source=stripe" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"id":"evt_1","type":"charge.succeeded","data":{"object":{"id":"ch_1","amount":2500,"customer":"cus_1"}}}'
```

### Response Format (Canonical Event)
```json
{
  "event_id": "evt_1",
  "source": "stripe", 
  "occurred_at": "2024-08-11T12:00:00+00:00",
  "actor": {"id": "cus_1"},
  "subject": {"type": "charge", "id": "ch_1"},
  "action": "charge.succeeded",
  "metadata": {"amount": 2500},
  "trace": [{"op": "map", "field": "amount", "from": "amount", "to": "amount"}]
}
```

## JSON Normalization

### Supported Schemas
- `contacts` - Email, phone, name normalization

### Usage
```bash
curl -X POST "http://localhost:8080/v1/json/normalize?schema=contacts" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"Email":"USER@EXAMPLE.COM","Name":"Doe, Jane","Phone":"(555) 123-4567"}'
```

### Response Format
```json
{
  "email": "user@example.com",
  "phone": "5551234567", 
  "first_name": "Jane",
  "last_name": "Doe",
  "company": null,
  "trace": [
    {"op": "lower", "field": "email"},
    {"op": "digits", "field": "phone"},
    {"op": "split_name", "field": "name"}
  ]
}
```

## SDK Schemas

### Contacts Schema
**Fields:** `email`, `phone`, `first_name`, `last_name`, `company`

**Synonyms:**
- email: email, e-mail, mail, email address
- phone: phone, phone number, tel, telephone  
- first_name: first, first name, fname, given name
- last_name: last, last name, lname, surname, family name
- company: company, organization, org, employer

### Transactions Schema  
**Fields:** `id`, `amount`, `currency`, `occurred_at`, `customer_id`

### Products Schema
**Fields:** `sku`, `name`, `price`, `currency`, `category`, `weight_kg`, `length_m`

**Unit Conversions:**
- Weight: lb, g, kg → kg
- Length: ft, in, m, km → m

## SDK CLI Commands

```bash
# Basic usage
python -m ingresskit.cli --in input.csv --out output.csv --schema contacts

# With tenant ID
python -m ingresskit.cli --in data.csv --out clean.csv --schema transactions --tenant-id company_123

# Available schemas: contacts, transactions, products
```

## SDK Programmatic Usage

```python
from ingresskit.repair import Repairer, Schema

# Initialize
repairer = Repairer(schema=Schema.contacts(), tenant_id="tenant_1")

# Process file
result = repairer.repair_file("messy_contacts.csv")

# Save results
result.save("clean_contacts.csv")

# Check results
print(f"Processed: {result.summary['rows_in']} → {result.summary['rows_out']} rows")
print(f"Sample diffs: {result.sample_diffs}")
```

## Error Codes

| Code | Description | Solution |
|------|-------------|----------|
| `400` | Bad request | Check JSON format, schema/source params |
| `401` | Unauthorized | Provide valid API key or admin token |
| `402` | Payment required | Add credits to API key |
| `500` | Server error | Check server logs, configuration |

## Configuration Environment Variables

### Required for Production
```bash
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
INGRESSKIT_ADMIN_TOKEN=admin_secret_123
```

### Optional Configuration
```bash
INGRESSKIT_API_KEYS=key1:1000,key2:5000
INGRESSKIT_FREE_PER_DAY=100
INGRESSKIT_PRICE_MAP=price_123:5000,price_456:20000
CHECKOUT_SUCCESS_URL=https://yourapp.com/success
CHECKOUT_CANCEL_URL=https://yourapp.com/cancel
```

## Common Patterns

### Check Credits Before Processing
```python
import requests

def check_credits(api_key):
    resp = requests.get(
        "http://localhost:8080/v1/billing/balance",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    return resp.json()["balance"] if resp.status_code == 200 else 0

balance = check_credits("your-api-key")
if balance > 10:
    # Proceed with processing
    pass
```

### Batch Webhook Processing
```python
webhooks = [stripe_payload1, stripe_payload2, stripe_payload3]
canonical_events = []

for payload in webhooks:
    resp = requests.post(
        "http://localhost:8080/v1/webhooks/ingest?source=stripe",
        headers={"Authorization": "Bearer your-api-key"},
        json=payload
    )
    if resp.status_code == 200:
        canonical_events.append(resp.json())
```

### CSV Processing Pipeline
```python
from ingresskit.repair import Repairer, Schema
import pandas as pd

# Process with IngressKit
repairer = Repairer(Schema.contacts())
result = repairer.repair_file("raw_contacts.csv")

# Convert to DataFrame for further processing
df = pd.DataFrame(result.rows_out)
df = df.dropna(subset=['email'])  # Remove rows without email

# Save final result
df.to_csv("final_contacts.csv", index=False)
```

## Testing Endpoints

### Test Webhook Processing
```bash
# Test data in server/fixtures/
curl -X POST "http://localhost:8080/v1/webhooks/ingest?source=stripe" \
  -H "Authorization: Bearer test-key" \
  -d @server/fixtures/stripe_charge_succeeded.json
```

### Test JSON Normalization
```bash
echo '{"Email":"TEST@EXAMPLE.COM","Name":"Smith, John"}' | \
curl -X POST "http://localhost:8080/v1/json/normalize?schema=contacts" \
  -H "Authorization: Bearer test-key" \
  -H "Content-Type: application/json" \
  -d @-
```

### Test Health
```bash
curl http://localhost:8080/ping
# Expected: {"message": "pong"}
```

---

*For detailed documentation, see PROJECT_OVERVIEW.md, SDK_REFERENCE.md, and SERVER_API_REFERENCE.md*
