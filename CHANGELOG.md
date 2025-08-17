# Changelog

All notable changes to IngressKit will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial open source release
- Self-hosted data repair toolkit
- Privacy-first architecture

## [0.1.0] - 2025-01-XX

### Added
- **CSV/Excel Repair SDK**
  - Smart header mapping with 40+ synonyms
  - Type coercion for emails, phones, dates, currencies
  - Unit conversion (mass: lb→kg, length: ft→m)
  - Complete audit trails and transformation logs
  - Support for contacts, transactions, and products schemas

- **FastAPI Server**
  - Webhook harmonization for Stripe, GitHub, Slack
  - JSON normalization with schema validation
  - Self-hosted deployment (no external dependencies)
  - Health check endpoints for monitoring

- **Docker Support**
  - `pilothobs/ingresskit:latest` - Full server
  - `pilothobs/ingresskit:core-latest` - CLI only
  - Multi-stage builds for optimized images
  - Docker Compose for local development

- **CI/CD Pipeline**
  - GitHub Actions for testing and builds
  - Automated Docker image publishing
  - Multi-Python version testing (3.9-3.12)
  - Code linting and formatting checks

- **Documentation**
  - Comprehensive README with privacy-first messaging
  - CONTRIBUTING.md with schema templates
  - Full API documentation in docs/ directory
  - Real-world examples and use cases

- **Community Features**
  - IngressKit Data Challenge framework
  - Schema contribution process
  - Contributor recognition system

### Technical Details
- **Languages**: Python 3.9+
- **Framework**: FastAPI with uvicorn
- **Dependencies**: Minimal (no external API dependencies)
- **License**: MIT
- **Performance**: 10,000+ CSV rows/second, 1,000+ webhook requests/second

### Supported Schemas
- **Contacts**: `email`, `phone`, `first_name`, `last_name`, `company`
- **Transactions**: `id`, `amount`, `currency`, `occurred_at`, `customer_id`
- **Products**: `sku`, `name`, `price`, `category`, `weight_kg`, `length_m`

### Supported Webhook Sources
- **Stripe**: Payment events, subscription changes
- **GitHub**: Issue events, PR events, repository events
- **Slack**: Message events, user events

[Unreleased]: https://github.com/pilothobs/ingresskit/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/pilothobs/ingresskit/releases/tag/v0.1.0
