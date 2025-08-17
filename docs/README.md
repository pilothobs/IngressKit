# IngressKit Documentation

Welcome to the comprehensive documentation for IngressKit - a lightweight data ingestion toolkit that normalizes and harmonizes messy data from multiple sources.

## 📚 Documentation Index

### Getting Started
- **[Project Overview](PROJECT_OVERVIEW.md)** - Complete introduction to IngressKit's capabilities, architecture, and use cases
- **[Quick API Reference](QUICK_API_REFERENCE.md)** - Fast reference for common API calls and CLI commands

### Technical Documentation
- **[Python SDK Reference](SDK_REFERENCE.md)** - Complete guide to the CSV/Excel repair SDK
- **[Server API Reference](SERVER_API_REFERENCE.md)** - Detailed FastAPI server endpoints and webhook processing
- **[Examples and Use Cases](EXAMPLES_AND_USE_CASES.md)** - Real-world examples and integration patterns
- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Production deployment, scaling, and maintenance

## 🚀 Quick Start

### 1. Install and Run the SDK
```bash
cd sdk/python
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m ingresskit.cli --in ../../examples/contacts_messy.csv --out clean.csv --schema contacts
```

### 2. Start the Server
```bash
cd server
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8080
```

### 3. Test the API
```bash
# Process a webhook
curl -X POST "http://localhost:8080/v1/webhooks/ingest?source=stripe" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"id":"evt_1","type":"charge.succeeded","data":{"object":{"id":"ch_1","amount":2500}}}'

# Normalize JSON data
curl -X POST "http://localhost:8080/v1/json/normalize?schema=contacts" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"Email":"USER@EXAMPLE.COM","Name":"Doe, Jane"}'
```

## 🎯 What IngressKit Does

### CSV/Excel Repair SDK
- **Smart Header Mapping**: Automatically maps messy column names to canonical schemas
- **Type Coercion**: Cleans and normalizes data types (emails, phones, dates, currencies)
- **Unit Conversion**: Converts between measurement units (lb→kg, ft→m)
- **Audit Trails**: Complete transformation logs for compliance and debugging

### Webhook Harmonizer
- **Multi-Provider Support**: Stripe, GitHub, Slack webhooks → unified format
- **Canonical Events**: Consistent event structure across all sources
- **API Key Management**: Secure access control with credit system
- **Stripe Integration**: Built-in billing and payment processing

### JSON Normalizer
- **Schema Validation**: Repairs LLM/API outputs to strict schemas
- **Field Cleaning**: Standardizes contact data, handles name parsing
- **Error Handling**: Graceful degradation with detailed error reporting

## 📖 Documentation Guide

### For Developers
1. Start with **[Project Overview](PROJECT_OVERVIEW.md)** to understand the architecture
2. Use **[SDK Reference](SDK_REFERENCE.md)** for CSV processing integration
3. Check **[Examples](EXAMPLES_AND_USE_CASES.md)** for implementation patterns

### For DevOps/Infrastructure
1. Review **[Deployment Guide](DEPLOYMENT_GUIDE.md)** for production setup
2. Use **[Server API Reference](SERVER_API_REFERENCE.md)** for configuration details
3. Check monitoring and scaling sections for production operations

### For API Users
1. Use **[Quick API Reference](QUICK_API_REFERENCE.md)** for immediate needs
2. Refer to **[Server API Reference](SERVER_API_REFERENCE.md)** for detailed endpoint docs
3. Check **[Examples](EXAMPLES_AND_USE_CASES.md)** for integration patterns

## 🔧 Core Capabilities

### Supported Data Sources
- **CSV/Excel Files**: Any structure, messy headers, mixed data types
- **Stripe Webhooks**: Payment events, subscription changes
- **GitHub Webhooks**: Issue events, PR events, repository events  
- **Slack Webhooks**: Message events, user events
- **JSON Payloads**: LLM outputs, third-party API responses

### Supported Schemas
- **Contacts**: `email`, `phone`, `first_name`, `last_name`, `company`
- **Transactions**: `id`, `amount`, `currency`, `occurred_at`, `customer_id`
- **Products**: `sku`, `name`, `price`, `category`, `weight_kg`, `length_m`

### Key Features
- ✅ **Deterministic**: Same input always produces same output
- ✅ **Extensible**: Easy to add custom schemas and transformations
- ✅ **Production-Ready**: Docker deployment, monitoring, scaling support
- ✅ **Audit-Friendly**: Complete transformation logs and error tracking
- ✅ **Multi-Tenant**: Isolated processing per tenant/customer

## 🏗️ Architecture Overview

```
Input Sources          Processing Layer         Output Format
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   CSV/Excel    │───▶│   Python SDK     │───▶│ Clean CSV Files │
│   Files         │    │   (Repairer)     │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘

┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Webhooks      │───▶│  FastAPI Server  │───▶│ Canonical       │
│ (Multi-source)  │    │  (Harmonizer)    │    │ Events          │
└─────────────────┘    └──────────────────┘    └─────────────────┘

┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   JSON Data     │───▶│ JSON Normalizer  │───▶│ Validated       │
│ (LLM/3rd-party) │    │                  │    │ JSON Objects    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🌟 Use Cases

### E-commerce Platforms
- Import customer lists from various sources
- Normalize product catalogs with unit conversions
- Process payment webhooks from multiple providers

### SaaS Applications  
- Customer data onboarding from CSV uploads
- Multi-tenant data processing with isolation
- Real-time webhook event processing

### Financial Services
- Transaction monitoring across payment providers
- Compliance reporting with audit trails
- Data normalization for fraud detection

### Data Integration
- ETL pipeline preprocessing
- API response normalization
- LLM output validation and cleaning

## 📊 Performance & Scaling

### Throughput
- **CSV Processing**: 10,000+ rows/second (typical)
- **Webhook Processing**: 1,000+ requests/second (single instance)
- **JSON Normalization**: 500+ requests/second

### Scaling Options
- **Horizontal**: Multiple server instances with load balancing
- **Vertical**: Multi-core processing, increased memory
- **Database**: Migrate from file storage to PostgreSQL/Redis
- **Caching**: Add Redis for frequently accessed data

## 🔒 Security & Compliance

### Security Features
- API key-based authentication
- Request size and rate limiting
- HTTPS/TLS encryption
- Input validation and sanitization
- Secure error handling (no data leakage)

### Compliance Support
- Complete audit trails for all transformations
- Data retention controls
- Per-tenant data isolation
- Deterministic processing for reproducibility

## 🤝 Contributing

IngressKit is open source under the MIT License. Contributions are welcome!

### Development Setup
```bash
# Clone and set up development environment
git clone <repository-url>
cd IngressKit

# Set up SDK development
cd sdk/python
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Set up server development  
cd ../server
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### Running Tests
```bash
# SDK tests
cd sdk/python
python -m pytest

# Server tests
cd server  
python -m pytest tests/
```

## 📝 License

MIT License - see [LICENSE](../LICENSE) file for details.

## 📞 Support

- **Documentation Issues**: Check existing docs or open an issue
- **Bug Reports**: Use GitHub issues with detailed reproduction steps
- **Feature Requests**: Open GitHub issue with use case description
- **Security Issues**: Contact maintainers directly

---

**IngressKit**: Making messy data fit your application's needs, one transformation at a time.

*Last updated: January 2025*
