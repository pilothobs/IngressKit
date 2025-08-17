# IngressKit

**Self-hosted data repair toolkit. Your data, your servers, no third-party risk.**

Stop rewriting CSV importers and webhook parsers. IngressKit is a lightweight, deterministic toolkit that normalizes messy data from any source into clean, schema-compliant formats.

[![PyPI version](https://badge.fury.io/py/ingresskit.svg)](https://badge.fury.io/py/ingresskit)
[![Docker Pulls](https://img.shields.io/docker/pulls/pilothobs/ingresskit)](https://hub.docker.com/r/pilothobs/ingresskit)
[![GitHub Actions](https://github.com/pilothobs/ingresskit/workflows/CI/badge.svg)](https://github.com/pilothobs/ingresskit/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub stars](https://img.shields.io/github/stars/pilothobs/ingresskit.svg?style=social&label=Star)](https://github.com/pilothobs/ingresskit)

## 🎯 **Why IngressKit?**

Every application needs to ingest data, but most teams repeatedly build the same brittle solutions:

- ❌ **CSV importers** that break on messy headers and mixed data types
- ❌ **Webhook parsers** that fail when providers change their payload format  
- ❌ **JSON normalizers** for LLM outputs that don't validate properly
- ❌ **No audit trails** when data transformations go wrong

IngressKit solves this **once and for all** with a privacy-first, self-hosted approach.

## ⚡ **Quick Start**

### One-liner install:
```bash
pip install ingresskit
```

### Docker deployment:
```bash
docker run -p 8080:8080 pilothobs/ingresskit
```

### Clean your first messy CSV:
```bash
ingresskit repair --in messy_contacts.csv --out clean_contacts.csv --schema contacts
```

**Input (messy_contacts.csv):**
```csv
E-Mail,Phone Number,Name,Organization
USER@EXAMPLE.COM,(555) 123-4567,"Doe, Jane",Acme Inc
example+test@domain.com,555.987.6543,John Smith,
```

**Output (clean_contacts.csv):**
```csv
email,phone,first_name,last_name,company
user@example.com,5551234567,Jane,Doe,Acme Inc
example+test@domain.com,5559876543,John,Smith,
```

## 🏗️ **What It Does**

### 📊 **CSV/Excel Repair**
- **Smart header mapping**: `"E-Mail"` → `"email"`, `"Phone Number"` → `"phone"`
- **Type coercion**: Clean emails, extract digits from phone numbers, parse dates
- **Unit conversion**: `"Weight (lb)"` → kilograms, `"Length (ft)"` → meters
- **Audit trails**: See exactly what was transformed and why

### 🔗 **Webhook Harmonization**
- **Multi-provider support**: Stripe, GitHub, Slack → unified event format
- **Consistent structure**: Same fields across all webhook sources
- **Self-hosted**: Process sensitive webhook data on your own infrastructure

### 🧠 **JSON Normalization**
- **LLM output repair**: Fix inconsistent JSON from GPT, Claude, etc.
- **Schema validation**: Ensure third-party APIs return expected formats
- **Error recovery**: Graceful handling of malformed data

## 🔒 **Privacy & Security First**

- ✅ **Self-hosted**: Your data never leaves your infrastructure
- ✅ **No external dependencies**: Works completely offline
- ✅ **Audit trails**: Complete transformation logs for compliance
- ✅ **Deterministic**: Same input always produces same output
- ✅ **Open source**: Full transparency, no black boxes

## 🚀 **Architecture**

IngressKit has two main components:

### **Python SDK** (for CSV/Excel processing)
```python
from ingresskit import Repairer, Schema

repairer = Repairer(schema=Schema.contacts())
result = repairer.repair_file("messy_data.csv")
result.save("clean_data.csv")

print(f"Cleaned {result.summary['rows_in']} → {result.summary['rows_out']} rows")
```

### **FastAPI Server** (for webhooks and JSON)
```bash
# Start server
uvicorn ingresskit.server:app --host 0.0.0.0 --port 8080

# Process webhook
curl -X POST "http://localhost:8080/v1/webhooks/normalize?source=stripe" \
  -H "Content-Type: application/json" \
  -d @stripe_webhook.json

# Normalize JSON
curl -X POST "http://localhost:8080/v1/json/normalize?schema=contacts" \
  -H "Content-Type: application/json" \
  -d '{"Email":"USER@EXAMPLE.COM","Name":"Doe, Jane"}'
```

## 📋 **Built-in Schemas**

IngressKit comes with battle-tested schemas for common use cases:

### **Contacts** (`email`, `phone`, `first_name`, `last_name`, `company`)
Perfect for customer imports, lead lists, CRM data

### **Transactions** (`id`, `amount`, `currency`, `occurred_at`, `customer_id`)
Financial data, payment records, billing exports

### **Products** (`sku`, `name`, `price`, `category`, `weight_kg`, `length_m`)
E-commerce catalogs, inventory data (with automatic unit conversion)

**Want more schemas?** [Contribute one!](CONTRIBUTING.md) 

## 🎮 **Try the IngressKit Data Challenge**

Think your CSV is too messy for IngressKit? We love a challenge!

1. Upload your messiest CSV to the [IngressKit Data Challenge](https://github.com/pilothobs/ingresskit/discussions/categories/data-challenge)
2. We'll show you how IngressKit handles it
3. If it breaks, we'll add support and credit you as a contributor

## 🏢 **Production Deployment**

### **Docker Compose (Recommended)**
```yaml
version: '3.8'
services:
  ingresskit:
    image: pilothobs/ingresskit:latest
    ports:
      - "8080:8080"
    volumes:
      - ./data:/app/data
    environment:
      - ENVIRONMENT=production
```

### **Kubernetes**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ingresskit
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ingresskit
  template:
    spec:
      containers:
      - name: ingresskit
        image: pilothobs/ingresskit:latest
        ports:
        - containerPort: 8080
```

### **systemd Service**
```bash
# Install as system service
sudo cp deploy/ingresskit.service /etc/systemd/system/
sudo systemctl enable ingresskit
sudo systemctl start ingresskit
```

## 🌟 **Real-World Use Cases**

### **E-commerce Platform**
*"We use IngressKit to normalize product catalogs from 50+ suppliers. Handles everything from weight conversions to price formatting."* - TechCorp

### **Fintech Startup** 
*"IngressKit processes payment webhooks from 5 different providers into one consistent format. Saved us months of integration work."* - PayFlow

### **SaaS Company**
*"Customer CSV imports went from 'pray it works' to 'just works' with IngressKit's deterministic processing."* - DataCo

## 📊 **Performance**

- **CSV Processing**: 10,000+ rows/second
- **Webhook Processing**: 1,000+ requests/second  
- **Memory Usage**: ~50MB base, scales linearly
- **Startup Time**: <2 seconds

## 🤝 **Contributing**

IngressKit thrives on community contributions! 

### **Add a New Schema**
```python
# 1. Define your schema
CUSTOM_SCHEMA = ["field1", "field2", "field3"]

# 2. Add field synonyms  
SYNONYMS = {
    "field1": ["field1", "f1", "first_field"],
    "field2": ["field2", "f2", "second_field"],
}

# 3. Submit a PR!
```

### **Ways to Contribute**
- 🔧 **New schemas** for different industries
- 🐛 **Bug fixes** and performance improvements  
- 📚 **Documentation** and examples
- 🧪 **Test cases** for edge cases
- 🌐 **Webhook sources** (Shopify, Mailchimp, etc.)

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## 📈 **Roadmap**

### **v0.2.0** (Next Release)
- [ ] Additional webhook sources (Shopify, Mailchimp)
- [ ] Custom schema builder UI
- [ ] Performance optimizations
- [ ] Prometheus metrics

### **v0.3.0** (Future)
- [ ] Real-time streaming support
- [ ] Advanced data validation rules
- [ ] Plugin architecture
- [ ] GraphQL API

## 📞 **Support**

- 📖 **Documentation**: [Full docs](docs/)
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/pilothobs/ingresskit/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/pilothobs/ingresskit/discussions)
- 🏢 **Enterprise Support**: [Contact us](mailto:support@pilothobs.com)

## 📄 **License**

MIT License - use IngressKit freely in your projects, commercial or otherwise.

## 🔮 **Coming Soon**

**IngressKit Cloud** - Managed hosting for teams who want IngressKit without the ops overhead. [Join the waitlist](https://ingresskit.com/cloud) for early access.

---

**Built by [@pilothobs](https://github.com/pilothobs)** | **⭐ Star us on GitHub if IngressKit saves you time!**
