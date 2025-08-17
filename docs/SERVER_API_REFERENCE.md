# IngressKit Server API Reference

## Overview

The IngressKit FastAPI server provides webhook harmonization, JSON normalization, and billing management through a RESTful API. It transforms diverse webhook payloads into canonical event formats and normalizes JSON data according to predefined schemas.

## Base Configuration

### Server Details
- **Framework**: FastAPI 0.112.0+
- **Server**: uvicorn
- **Default Port**: 8080
- **API Version**: v1
- **Documentation**: Available at `/docs` (Swagger UI)

### CORS Configuration
Allowed origins:
- `https://www.ingresskit.com`
- `https://ingresskit.com`
- `https://ingresskit.dev`
- `http://localhost:3000`
- `http://localhost:5173`

## Authentication

### API Key Authentication
All protected endpoints require Bearer token authentication:

```bash
Authorization: Bearer your-api-key
```

### Key Management
- Keys are managed through the internal KeyStore system
- Credits are tracked per API key
- Free tier available for unknown keys (configurable)

## Core Endpoints

### Health Check

#### `GET /ping` or `GET /v1/ping`
Simple health check endpoint.

**Response:**
```json
{
  "message": "pong"
}
```

**Example:**
```bash
curl http://localhost:8080/ping
```

### Root Endpoint

#### `GET /`
Serves static splash page or default HTML.

**Response:** HTML content from `static/index.html` or default message.

## Webhook Processing

### Webhook Ingestion

#### `POST /v1/webhooks/ingest`
Processes webhooks from supported providers and converts them to canonical event format.

**Parameters:**
- `source` (query): Webhook source (`stripe`, `github`, `slack`)

**Headers:**
- `Authorization: Bearer {api_key}` (required)
- `Content-Type: application/json`

**Request Body:** Original webhook payload (varies by source)

**Response:** Canonical event object

**Example:**
```bash
curl -X POST "http://localhost:8080/v1/webhooks/ingest?source=stripe" \
  -H "Authorization: Bearer sk_test_123" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "evt_1234",
    "type": "charge.succeeded",
    "data": {
      "object": {
        "id": "ch_1234",
        "amount": 2500,
        "customer": "cus_1234"
      }
    },
    "created": 1723380000
  }'
```

**Response:**
```json
{
  "event_id": "evt_1234",
  "source": "stripe",
  "occurred_at": "2024-08-11T12:00:00+00:00",
  "actor": {"id": "cus_1234"},
  "subject": {"type": "charge", "id": "ch_1234"},
  "action": "charge.succeeded",
  "metadata": {"amount": 2500},
  "trace": [{"op": "map", "field": "amount", "from": "amount", "to": "amount"}]
}
```

### Supported Webhook Sources

#### Stripe Webhooks
**Supported Events:** All Stripe webhook events
**Key Mappings:**
- `event_id` ← `id`
- `actor.id` ← `data.object.customer`
- `subject` ← `data.object` (type and id)
- `action` ← `type`
- `occurred_at` ← `created` (timestamp)

**Example Stripe Payload:**
```json
{
  "id": "evt_1234",
  "type": "charge.succeeded",
  "data": {
    "object": {
      "id": "ch_1234",
      "object": "charge",
      "amount": 2500,
      "customer": "cus_1234"
    }
  },
  "created": 1723380000
}
```

#### GitHub Webhooks
**Supported Events:** Issue events, PR events, repository events
**Key Mappings:**
- `actor` ← `sender` (id and login)
- `subject` ← `issue` or relevant object
- `action` ← `action`
- `metadata` ← Issue/PR details

**Example GitHub Payload:**
```json
{
  "action": "opened",
  "issue": {
    "id": 123,
    "number": 456,
    "title": "Bug: crash on launch",
    "html_url": "https://github.com/user/repo/issues/456"
  },
  "sender": {
    "id": 789,
    "login": "username"
  }
}
```

#### Slack Webhooks
**Supported Events:** Message events, user events
**Key Mappings:**
- `actor.id` ← `event.user`
- `subject` ← Channel and event type info
- `action` ← `event.type`
- `metadata` ← Event details

**Example Slack Payload:**
```json
{
  "event_id": "evt_123",
  "event_time": 1723380000,
  "event": {
    "type": "message",
    "user": "U123456",
    "channel": "C123456",
    "text": "Hello world"
  }
}
```

## JSON Normalization

### JSON Schema Normalization

#### `POST /v1/json/normalize`
Normalizes JSON data according to predefined schemas.

**Parameters:**
- `schema` (query): Target schema (`contacts`)

**Headers:**
- `Authorization: Bearer {api_key}` (required)
- `Content-Type: application/json`

**Request Body:** JSON object to normalize

**Response:** Normalized JSON object with trace information

**Example:**
```bash
curl -X POST "http://localhost:8080/v1/json/normalize?schema=contacts" \
  -H "Authorization: Bearer sk_test_123" \
  -H "Content-Type: application/json" \
  -d '{
    "Email": "USER@EXAMPLE.COM",
    "Phone": "(555) 123-4567",
    "Name": " Doe, Jane "
  }'
```

**Response:**
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

### Supported Normalization Schemas

#### Contacts Schema
**Input Fields:** Flexible (Email, email, Name, name, Phone, phone, etc.)
**Output Fields:**
- `email`: Lowercase, trimmed
- `phone`: Digits only
- `first_name`: Extracted from name
- `last_name`: Extracted from name
- `company`: Always null (placeholder)

**Name Parsing Rules:**
- Comma format: `"Last, First"` → splits on comma
- Space format: `"First Last"` → splits on first space
- Single name: Assigned to first_name

## Billing & Credits

### Balance Check

#### `GET /v1/billing/balance`
Returns current credit balance for the authenticated API key.

**Headers:**
- `Authorization: Bearer {api_key}` (required)

**Response:**
```json
{
  "api_key": "sk_test_123",
  "balance": 9950
}
```

**Example:**
```bash
curl -H "Authorization: Bearer sk_test_123" \
  http://localhost:8080/v1/billing/balance
```

### Stripe Checkout

#### `POST /v1/billing/create_checkout`
Creates a Stripe checkout session for purchasing credits.

**Request Body:**
```json
{
  "price_id": "price_1234",
  "api_key": "sk_test_123",
  "mode": "payment",
  "success_url": "https://yourapp.com/success",
  "cancel_url": "https://yourapp.com/cancel"
}
```

**Response:**
```json
{
  "url": "https://checkout.stripe.com/pay/cs_test_..."
}
```

**Example:**
```bash
curl -X POST http://localhost:8080/v1/billing/create_checkout \
  -H "Content-Type: application/json" \
  -d '{
    "price_id": "price_1234",
    "api_key": "sk_test_123",
    "mode": "payment"
  }'
```

### Stripe Webhook Handler

#### `POST /v1/billing/webhook`
Handles Stripe webhooks for automatic credit provisioning.

**Headers:**
- `stripe-signature`: Stripe webhook signature (for verification)

**Supported Events:**
- `checkout.session.completed`: Automatically adds credits to API key

**Configuration Required:**
- `STRIPE_WEBHOOK_SECRET`: For signature verification
- `INGRESSKIT_PRICE_MAP`: Maps Stripe price IDs to credit amounts

### Price Resolution

#### `GET /v1/billing/resolve`
Resolves price aliases to actual Stripe price IDs.

**Parameters:**
- `name` (query): Price alias name

**Response:**
```json
{
  "input": "price_small",
  "resolved": "price_live_123",
  "aliases": {
    "price_small": "price_live_123",
    "price_med": "price_live_456"
  }
}
```

## Admin Endpoints

### Credit Management

#### `POST /v1/admin/credit`
Manually add credits to an API key (admin only).

**Headers:**
- `X-Admin-Token: {admin_token}` (required)

**Request Body:**
```json
{
  "api_key": "sk_test_123",
  "amount": 5000
}
```

**Response:**
```json
{
  "api_key": "sk_test_123",
  "balance": 15000
}
```

**Example:**
```bash
curl -X POST http://localhost:8080/v1/admin/credit \
  -H "X-Admin-Token: admin_secret_123" \
  -H "Content-Type: application/json" \
  -d '{"api_key": "sk_test_123", "amount": 5000}'
```

## Data Models

### CanonicalEvent
Unified event structure for all webhook sources.

```python
{
  "event_id": str,           # Unique event identifier
  "source": str,             # Source system (stripe, github, slack)
  "occurred_at": str,        # ISO timestamp
  "actor": {                 # Entity that triggered the event
    "id": str,
    "login": str (optional)
  },
  "subject": {               # Entity the event is about
    "type": str,
    "id": str,
    "number": int (optional)
  },
  "action": str,             # Event action/type
  "metadata": dict,          # Additional event data
  "trace": [                 # Transformation audit trail
    {
      "op": str,
      "field": str,
      "from": str,
      "to": str
    }
  ]
}
```

### CheckoutRequest
Stripe checkout session creation request.

```python
{
  "price_id": str,           # Stripe price ID or alias
  "api_key": str,            # Target API key for credits
  "mode": str,               # "payment" or "subscription"
  "success_url": str,        # Redirect after success
  "cancel_url": str          # Redirect after cancel
}
```

### AdminCreditRequest
Admin credit adjustment request.

```python
{
  "api_key": str,            # Target API key
  "amount": int              # Credit amount to add
}
```

## Configuration

### Environment Variables

#### Required for Production
- `STRIPE_SECRET_KEY`: Stripe API secret key
- `STRIPE_WEBHOOK_SECRET`: Stripe webhook endpoint secret
- `INGRESSKIT_ADMIN_TOKEN`: Admin operations token

#### Credit System Configuration
- `INGRESSKIT_API_KEYS`: Seed API keys with credits (`key1:1000,key2:5000`)
- `INGRESSKIT_FREE_PER_DAY`: Free credits per day for unknown keys (default: 100)
- `INGRESSKIT_PRICE_MAP`: Maps Stripe prices to credits (`price_123:5000,price_456:20000`)
- `INGRESSKIT_PRICE_ALIASES`: Price aliases (`small:price_123,large:price_456`)

#### Checkout URLs
- `CHECKOUT_SUCCESS_URL`: Default success redirect
- `CHECKOUT_CANCEL_URL`: Default cancel redirect

### Data Storage
- **Location**: `server/data/balances.json`
- **Format**: JSON key-value store
- **Persistence**: Atomic writes with temporary files
- **Backup**: Manual file-based backup recommended

## Error Handling

### HTTP Status Codes
- `200`: Success
- `400`: Bad request (invalid JSON, unsupported schema/source)
- `401`: Unauthorized (missing/invalid API key or admin token)
- `402`: Payment required (out of credits)
- `500`: Server error

### Error Response Format
```json
{
  "detail": "Error description"
}
```

### Common Errors
- `"Missing API key"`: Authorization header missing or malformed
- `"Out of credits"`: API key has insufficient credits
- `"Invalid JSON"`: Request body is not valid JSON
- `"Unsupported source"`: Webhook source not recognized
- `"Unsupported schema"`: JSON normalization schema not available
- `"unauthorized"`: Admin token invalid

## Rate Limiting & Credits

### Credit Consumption
- **Webhook Processing**: 1 credit per request
- **JSON Normalization**: 1 credit per request
- **Other Endpoints**: No credits consumed

### Free Tier
- Unknown API keys get free daily credits (configurable)
- Known keys with 0 balance are rejected (402 error)

### Credit Management
- Credits persist across server restarts
- Atomic credit operations prevent race conditions
- Negative balances not allowed

## Integration Examples

### Webhook Integration
```python
import requests

# Set up webhook endpoint
webhook_url = "https://your-ingresskit-server.com/v1/webhooks/ingest"
api_key = "your-api-key"

# Process Stripe webhook
def handle_stripe_webhook(payload):
    response = requests.post(
        f"{webhook_url}?source=stripe",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json=payload
    )
    
    if response.status_code == 200:
        canonical_event = response.json()
        # Process canonical event
        return canonical_event
    else:
        # Handle error
        print(f"Error: {response.json()}")
```

### JSON Normalization
```python
import requests

# Normalize contact data
def normalize_contact(raw_contact):
    response = requests.post(
        "https://your-ingresskit-server.com/v1/json/normalize?schema=contacts",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json=raw_contact
    )
    
    return response.json()

# Usage
raw = {"Email": "USER@EXAMPLE.COM", "Name": "Doe, Jane"}
clean = normalize_contact(raw)
# Result: {"email": "user@example.com", "first_name": "Jane", ...}
```

### Credit Monitoring
```python
def check_credits(api_key):
    response = requests.get(
        "https://your-ingresskit-server.com/v1/billing/balance",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    
    if response.status_code == 200:
        balance = response.json()["balance"]
        if balance < 100:  # Low credit warning
            print(f"Warning: Only {balance} credits remaining")
        return balance
    return None
```

## Testing

### Test Files
Located in `server/tests/`:
- `test_ping.py`: Health check tests
- `test_webhooks.py`: Webhook processing tests
- `test_webhooks.http`: HTTP client test requests

### Test Fixtures
Located in `server/fixtures/`:
- `stripe_charge_succeeded.json`
- `github_issue_opened.json`
- `slack_message.json`

### Running Tests
```bash
cd server
python -m pytest tests/
```

### Manual Testing
```bash
# Test webhook processing
curl -X POST "http://localhost:8080/v1/webhooks/ingest?source=stripe" \
  -H "Authorization: Bearer test-key" \
  -H "Content-Type: application/json" \
  -d @fixtures/stripe_charge_succeeded.json

# Test JSON normalization
curl -X POST "http://localhost:8080/v1/json/normalize?schema=contacts" \
  -H "Authorization: Bearer test-key" \
  -H "Content-Type: application/json" \
  -d '{"Email": "TEST@EXAMPLE.COM", "Name": "Smith, John"}'
```

## Performance Considerations

### Throughput
- **Webhook Processing**: ~1000 requests/second (single instance)
- **JSON Normalization**: ~500 requests/second (depends on complexity)
- **Credit Operations**: Atomic file operations (bottleneck for high concurrency)

### Scaling Recommendations
- **Horizontal Scaling**: Multiple server instances with shared storage
- **Database Migration**: Replace JSON file storage with PostgreSQL/Redis
- **Caching**: Add Redis for frequently accessed data
- **Load Balancing**: nginx or cloud load balancer

### Memory Usage
- **Base Memory**: ~50MB per server instance
- **Per Request**: ~1-5MB depending on payload size
- **Credit Store**: Minimal (JSON file cached in memory)

## Security Best Practices

### API Key Management
- Use strong, randomly generated API keys
- Rotate keys regularly
- Monitor usage patterns for anomalies
- Implement key scoping (future feature)

### Webhook Security
- Verify webhook signatures when possible
- Use HTTPS for all communications
- Implement request size limits
- Log security events

### Data Privacy
- Webhook payloads are not persisted
- Credit balances stored locally (consider encryption)
- No sensitive data in logs
- CORS restrictions for browser access

---

*For deployment instructions and production configuration, see the Deployment Guide.*
