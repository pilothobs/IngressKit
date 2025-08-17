# IngressKit - Project Overview

## What is IngressKit?

IngressKit is a lightweight, deterministic data ingestion toolkit designed to normalize and harmonize messy data from multiple sources. It provides a unified approach to handling CSV imports, webhook processing, and JSON normalization with built-in schema validation and transformation capabilities.

**Tagline:** *"Make anything fit. Files, webhooks, and AI outputs normalized."*

## Problem Statement

Every application needs to ingest data, but most teams repeatedly reimplement:
- CSV/Excel importers that handle messy, inconsistent formats
- Webhook parsers for different service providers (Stripe, GitHub, Slack)
- JSON normalizers for LLM or third-party API outputs

IngressKit provides a lightweight, deterministic alternative with per-tenant memory that improves over time.

## Core Components

### 1. Python SDK (`sdk/python/`)
**CSV/Excel Import Repair Library**
- Cleans, maps, and validates messy files into canonical schemas
- Provides deterministic transformations with audit trails
- Supports unit conversions and field normalization
- CLI tool for batch processing

### 2. FastAPI Server (`server/`)
**Webhook Harmonizer + JSON Normalizer**
- Unified webhook processing for multiple providers
- JSON schema normalization and repair
- API key authentication with credit system
- Stripe integration for billing
- Docker-ready deployment

### 3. Documentation & Examples
**Comprehensive guides and samples**
- Example CSV files (messy → clean transformations)
- API usage examples
- Deployment guides

## Key Features

### 🔧 Data Repair & Normalization
- **Header Mapping**: Intelligent field mapping using synonyms and fuzzy matching
- **Type Coercion**: Automatic data type conversion and validation
- **Unit Conversion**: Built-in support for mass (kg) and length (m) normalization
- **Error Handling**: Graceful handling of malformed data with detailed error reporting

### 🌐 Webhook Harmonization
- **Multi-Provider Support**: Stripe, GitHub, Slack webhooks → unified format
- **Canonical Events**: Consistent event structure across all sources
- **Idempotent Processing**: Safe to replay webhook events
- **Metadata Preservation**: Original payload data retained for audit

### 📝 Schema Management
- **Predefined Schemas**: contacts, transactions, products
- **Extensible Design**: Easy to add custom schemas
- **Field Validation**: Type checking and constraint enforcement
- **Transformation Logs**: Complete audit trail of all changes

### 💳 Enterprise Features
- **API Key Management**: Secure access control
- **Credit System**: Usage-based billing integration
- **Stripe Integration**: Automated payment processing
- **Multi-tenant Support**: Isolated processing per tenant

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   CSV/Excel    │    │   Webhooks       │    │   JSON Data     │
│   Files         │    │   (Multi-source) │    │   (LLM/3rd-party)│
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Python SDK    │    │  FastAPI Server  │    │  JSON Normalizer│
│   (Repairer)    │    │  (Harmonizer)    │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Canonical Schemas                            │
│   • contacts: email, phone, first_name, last_name, company     │
│   • transactions: id, amount, currency, occurred_at, customer  │
│   • products: sku, name, price, category, weight_kg, length_m  │
└─────────────────────────────────────────────────────────────────┘
```

## Supported Data Sources

### Input Formats
- **CSV/Excel Files**: Any structure, messy headers, mixed data types
- **Stripe Webhooks**: charge.succeeded, subscription events, etc.
- **GitHub Webhooks**: issue events, PR events, repository events
- **Slack Webhooks**: message events, user events
- **JSON Payloads**: LLM outputs, third-party API responses

### Output Formats
- **Clean CSV**: Normalized, schema-compliant tabular data
- **Canonical Events**: Unified webhook event structure
- **Validated JSON**: Schema-compliant JSON objects

## Quick Start Examples

### Python SDK Usage
```bash
cd sdk/python
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m ingresskit.cli --in messy.csv --out clean.csv --schema contacts
```

### Server Deployment
```bash
cd server
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8080
```

### API Usage
```bash
# Webhook processing
curl -X POST "http://localhost:8080/v1/webhooks/ingest?source=stripe" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"id":"evt_1","type":"charge.succeeded",...}'

# JSON normalization
curl -X POST "http://localhost:8080/v1/json/normalize?schema=contacts" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"Email":"USER@EXAMPLE.COM","Name":"Doe, Jane"}'
```

## Use Cases

### 1. Customer Data Import
- Import customer lists from various sources (CRM exports, lead lists)
- Normalize contact information (emails, phone numbers, names)
- Handle different CSV formats and column naming conventions

### 2. Financial Transaction Processing
- Process payment data from multiple providers
- Normalize currency, amounts, and date formats
- Maintain audit trails for compliance

### 3. Product Catalog Management
- Import product data with unit conversions
- Handle different measurement systems (metric/imperial)
- Normalize pricing and categorization

### 4. Event Stream Processing
- Unify webhook events from multiple services
- Create consistent event logs across platforms
- Enable downstream processing with predictable data structures

## Technical Specifications

### Requirements
- **Python**: 3.9+
- **Dependencies**: FastAPI, Pydantic, python-dateutil, Stripe SDK
- **Database**: File-based JSON storage (production-ready for moderate scale)
- **Authentication**: API key-based with Bearer token support

### Performance
- **Throughput**: Optimized for moderate-scale data processing
- **Memory**: Efficient streaming processing for large CSV files
- **Latency**: Sub-second response times for webhook processing

### Security
- **Authentication**: API key validation
- **CORS**: Configurable cross-origin policies
- **Input Validation**: Comprehensive payload validation
- **Error Handling**: Secure error messages without data leakage

## Deployment Options

### Local Development
- Python virtual environment
- Direct uvicorn server
- File-based configuration

### Docker Deployment
- Multi-stage Docker build
- Environment variable configuration
- Health check endpoints

### Production Deployment
- systemd service integration
- Reverse proxy support (nginx)
- Log rotation and monitoring
- Backup and recovery procedures

## Extensibility

### Adding New Schemas
1. Define canonical field list in `CANONICAL_SCHEMAS`
2. Add field synonyms to `HEADER_SYNONYMS`
3. Implement custom coercion logic in `_coerce_value()`
4. Update server endpoints for JSON normalization

### Adding New Webhook Sources
1. Implement normalization function (e.g., `normalize_custom()`)
2. Add source routing in `/v1/webhooks/ingest` endpoint
3. Define canonical event mapping
4. Add test fixtures and validation

### Custom Field Types
1. Extend coercion logic for new data types
2. Add unit conversion functions if needed
3. Update schema definitions
4. Implement validation rules

## License & Contributing

- **License**: MIT License (see LICENSE file)
- **Copyright**: 2025 pilothobs
- **Contributing**: Open to contributions following standard GitHub workflow

## Next Steps

1. **Explore Examples**: Check `examples/` directory for sample data transformations
2. **API Reference**: See detailed endpoint documentation
3. **Deployment Guide**: Follow production deployment instructions
4. **Custom Integration**: Extend schemas and sources for your use case

---

*IngressKit: Making messy data fit your application's needs, one transformation at a time.*
