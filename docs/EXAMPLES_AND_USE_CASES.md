# IngressKit Examples and Use Cases

## Overview

This guide provides comprehensive examples of using IngressKit for common data ingestion scenarios. Each example includes sample data, processing steps, and expected outputs.

## Table of Contents
1. [CSV/Excel Processing Examples](#csvexcel-processing-examples)
2. [Webhook Integration Examples](#webhook-integration-examples)
3. [JSON Normalization Examples](#json-normalization-examples)
4. [Real-World Use Cases](#real-world-use-cases)
5. [Integration Patterns](#integration-patterns)

## CSV/Excel Processing Examples

### Example 1: Customer Contact Import

**Scenario:** Import messy customer contact data from various sources into a standardized format.

**Input Data** (`examples/contacts_messy.csv`):
```csv
E-Mail,Phone Number,Name,Organization
USER@EXAMPLE.COM,(555) 123-4567,"Doe, Jane",Acme Inc
example+test@domain.com,555.987.6543,John Smith,
```

**Processing:**
```bash
python -m ingresskit.cli \
  --in examples/contacts_messy.csv \
  --out examples/contacts_clean.csv \
  --schema contacts
```

**Output Data** (`examples/contacts_clean.csv`):
```csv
email,phone,first_name,last_name,company
user@example.com,5551234567,Jane,Doe,Acme Inc
example+test@domain.com,5559876543,John,Smith,
```

**Transformations Applied:**
- Email addresses converted to lowercase
- Phone numbers stripped to digits only
- Names parsed from "Last, First" format
- Headers mapped to canonical field names

### Example 2: Product Catalog with Unit Conversions

**Input Data** (`examples/products_with_units.csv`):
```csv
SKU,Product Name,Price,Weight (lb),Length (ft),Category
ABC123,Widget Pro,$29.99,2.5,1.2,Electronics
DEF456,Gadget Max,$149.95,5.0,2.8,Tools
```

**Processing:**
```python
from ingresskit.repair import Repairer, Schema

repairer = Repairer(schema=Schema.products(), tenant_id="store_1")
result = repairer.repair_file("examples/products_with_units.csv")
result.save("examples/products_clean.csv")

print("Processing Summary:")
print(f"Rows: {result.summary['rows_in']} → {result.summary['rows_out']}")
print("Sample transformations:", result.sample_diffs[0])
```

**Output:**
```csv
sku,name,price,currency,category,weight_kg,length_m
ABC123,Widget Pro,29.99,,Electronics,1.133981,0.365760
DEF456,Gadget Max,149.95,,Tools,2.267962,0.853440
```

**Transformations Applied:**
- Prices extracted from currency-formatted strings
- Weight converted from pounds to kilograms (lb × 0.45359237)
- Length converted from feet to meters (ft × 0.3048)
- Headers normalized to canonical names

### Example 3: Financial Transaction Processing

**Input Data** (`examples/transactions_messy.csv`):
```csv
Transaction ID,Amount (USD),Date,Customer
TXN-001,$1,234.56,2024/08/15,CUST_123
TXN-002,€567.89,15-Aug-2024,CUST_456
TXN-003,¥12345,Aug 15 2024,CUST_789
```

**Processing:**
```python
from ingresskit.repair import Repairer, Schema

repairer = Repairer(schema=Schema.transactions())
result = repairer.repair_file("examples/transactions_messy.csv")

# Inspect transformations
for i, diff in enumerate(result.sample_diffs):
    print(f"Row {i+1} transformations:")
    print(f"  Before: {diff['before']}")
    print(f"  After:  {diff['after']}")
    print()
```

**Expected Output:**
```csv
id,amount,currency,occurred_at,customer_id
TXN-001,1234.56,USD,2024-08-15,CUST_123
TXN-002,567.89,EUR,2024-08-15,CUST_456
TXN-003,12345.00,JPY,2024-08-15,CUST_789
```

## Webhook Integration Examples

### Example 1: Stripe Payment Processing

**Scenario:** Process Stripe payment webhooks and convert to canonical events for downstream processing.

**Input Webhook** (Stripe charge.succeeded):
```json
{
  "id": "evt_1NvjEKGPqGqKOjKV9vqZ7Xc1",
  "type": "charge.succeeded",
  "data": {
    "object": {
      "id": "ch_1NvjEKGPqGqKOjKV9vqZ7Xc1",
      "object": "charge",
      "amount": 2500,
      "currency": "usd",
      "customer": "cus_NvjEKGPqGqKOjKV9vqZ7Xc1",
      "description": "Subscription payment"
    }
  },
  "created": 1693526400
}
```

**Processing:**
```bash
curl -X POST "http://localhost:8080/v1/webhooks/ingest?source=stripe" \
  -H "Authorization: Bearer sk_test_123" \
  -H "Content-Type: application/json" \
  -d @stripe_webhook.json
```

**Canonical Event Output:**
```json
{
  "event_id": "evt_1NvjEKGPqGqKOjKV9vqZ7Xc1",
  "source": "stripe",
  "occurred_at": "2023-08-31T12:00:00+00:00",
  "actor": {
    "id": "cus_NvjEKGPqGqKOjKV9vqZ7Xc1"
  },
  "subject": {
    "type": "charge",
    "id": "ch_1NvjEKGPqGqKOjKV9vqZ7Xc1"
  },
  "action": "charge.succeeded",
  "metadata": {
    "amount": 2500,
    "currency": "usd",
    "description": "Subscription payment"
  },
  "trace": [
    {"op": "map", "field": "amount", "from": "amount", "to": "amount"}
  ]
}
```

### Example 2: GitHub Issue Tracking

**Scenario:** Track GitHub issue events across multiple repositories.

**Input Webhook** (GitHub issue opened):
```json
{
  "action": "opened",
  "issue": {
    "id": 1847436237,
    "number": 123,
    "title": "Bug: Application crashes on startup",
    "html_url": "https://github.com/myorg/myrepo/issues/123",
    "state": "open"
  },
  "repository": {
    "name": "myrepo",
    "full_name": "myorg/myrepo"
  },
  "sender": {
    "id": 12345,
    "login": "developer123"
  }
}
```

**Processing & Output:**
```json
{
  "event_id": "",
  "source": "github", 
  "occurred_at": "2024-01-15T10:30:00+00:00",
  "actor": {
    "id": 12345,
    "login": "developer123"
  },
  "subject": {
    "type": "issue",
    "id": 1847436237,
    "number": 123
  },
  "action": "opened",
  "metadata": {
    "title": "Bug: Application crashes on startup",
    "url": "https://github.com/myorg/myrepo/issues/123"
  },
  "trace": [
    {"op": "map", "field": "title", "from": "issue.title", "to": "metadata.title"}
  ]
}
```

### Example 3: Slack Message Processing

**Input Webhook** (Slack message event):
```json
{
  "event_id": "Ev06UBQR12345",
  "event_time": 1693526400,
  "event": {
    "type": "message",
    "user": "U123456789",
    "channel": "C987654321",
    "text": "Hello team! New feature deployed.",
    "ts": "1693526400.123456"
  }
}
```

**Canonical Output:**
```json
{
  "event_id": "Ev06UBQR12345",
  "source": "slack",
  "occurred_at": "2023-08-31T12:00:00+00:00",
  "actor": {
    "id": "U123456789"
  },
  "subject": {
    "type": "message",
    "channel": "C987654321"
  },
  "action": "message",
  "metadata": {
    "text": "Hello team! New feature deployed.",
    "ts": "1693526400.123456"
  },
  "trace": [
    {"op": "map", "field": "text", "from": "event.text", "to": "metadata.text"}
  ]
}
```

## JSON Normalization Examples

### Example 1: Contact Data Normalization

**Scenario:** Clean and normalize contact data from various sources (forms, APIs, LLM outputs).

**Input Variations:**
```python
# Web form data
form_data = {
    "Email": "USER@EXAMPLE.COM",
    "Phone": "(555) 123-4567", 
    "Name": " Doe, Jane "
}

# CRM export
crm_data = {
    "email": "john.smith@company.com",
    "phone": "555.987.6543",
    "name": "John Smith"
}

# LLM extracted data
llm_data = {
    "Email": "sarah.jones@startup.io",
    "Phone": "+1 (555) 456-7890",
    "Name": "Sarah Jones"
}
```

**Processing:**
```python
import requests

def normalize_contact(data):
    response = requests.post(
        "http://localhost:8080/v1/json/normalize?schema=contacts",
        headers={
            "Authorization": "Bearer your-api-key",
            "Content-Type": "application/json"
        },
        json=data
    )
    return response.json()

# Process all variations
results = [
    normalize_contact(form_data),
    normalize_contact(crm_data), 
    normalize_contact(llm_data)
]
```

**Normalized Outputs:**
```python
[
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
  },
  {
    "email": "john.smith@company.com",
    "phone": "5559876543",
    "first_name": "John",
    "last_name": "Smith",
    "company": null,
    "trace": [...]
  },
  {
    "email": "sarah.jones@startup.io", 
    "phone": "15554567890",
    "first_name": "Sarah",
    "last_name": "Jones",
    "company": null,
    "trace": [...]
  }
]
```

## Real-World Use Cases

### Use Case 1: E-commerce Customer Onboarding

**Business Problem:** Online store receives customer data from multiple sources (registration forms, social logins, CSV imports from partners) in inconsistent formats.

**Solution Architecture:**
```python
# Step 1: CSV import processing
from ingresskit.repair import Repairer, Schema
import pandas as pd

def process_partner_import(csv_file, partner_id):
    # Use IngressKit to clean CSV data
    repairer = Repairer(schema=Schema.contacts(), tenant_id=partner_id)
    result = repairer.repair_file(csv_file)
    
    # Convert to DataFrame for validation
    df = pd.DataFrame(result.rows_out)
    
    # Additional business logic
    df = df[df['email'].notna()]  # Require email
    df['source'] = f'partner_{partner_id}'
    df['imported_at'] = pd.Timestamp.now()
    
    return df

# Step 2: Real-time form normalization
import requests

def normalize_registration_form(form_data):
    # Clean form data through API
    response = requests.post(
        "https://api.yourstore.com/v1/json/normalize?schema=contacts",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json=form_data
    )
    
    if response.status_code == 200:
        clean_data = response.json()
        # Additional validation
        if not clean_data['email']:
            raise ValueError("Email required")
        return clean_data
    else:
        raise Exception(f"Normalization failed: {response.text}")

# Usage
partner_customers = process_partner_import("partner_leads.csv", "acme_corp")
form_customer = normalize_registration_form({
    "Email": "NEW.CUSTOMER@GMAIL.COM",
    "Name": "Smith, Bob",
    "Phone": "(555) 999-8888"
})
```

### Use Case 2: Financial Transaction Monitoring

**Business Problem:** Fintech company needs to process payment events from multiple providers (Stripe, PayPal, bank APIs) for fraud detection and reporting.

**Solution:**
```python
import requests
import json
from datetime import datetime

class TransactionProcessor:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.fintech-app.com"
    
    def process_webhook(self, source, payload):
        """Process webhook from any payment provider"""
        response = requests.post(
            f"{self.base_url}/v1/webhooks/ingest?source={source}",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json=payload
        )
        
        if response.status_code == 200:
            canonical_event = response.json()
            return self.analyze_transaction(canonical_event)
        else:
            raise Exception(f"Webhook processing failed: {response.text}")
    
    def analyze_transaction(self, event):
        """Analyze canonical event for fraud indicators"""
        analysis = {
            "event_id": event["event_id"],
            "source": event["source"],
            "timestamp": event["occurred_at"],
            "customer_id": event["actor"]["id"],
            "amount": event["metadata"].get("amount", 0),
            "risk_score": 0
        }
        
        # Risk scoring logic
        if analysis["amount"] > 10000:  # Large transaction
            analysis["risk_score"] += 30
        
        if event["source"] == "unknown_provider":
            analysis["risk_score"] += 20
            
        # Time-based analysis
        hour = datetime.fromisoformat(event["occurred_at"]).hour
        if hour < 6 or hour > 22:  # Off hours
            analysis["risk_score"] += 10
            
        analysis["risk_level"] = "high" if analysis["risk_score"] > 40 else "low"
        
        return analysis

# Usage with different payment providers
processor = TransactionProcessor("your-api-key")

# Stripe webhook
stripe_result = processor.process_webhook("stripe", stripe_webhook_payload)

# PayPal webhook (if supported)
# paypal_result = processor.process_webhook("paypal", paypal_webhook_payload)
```

### Use Case 3: Multi-tenant SaaS Data Import

**Business Problem:** SaaS platform allows customers to import their existing data via CSV uploads, but each customer has different column naming conventions.

**Solution:**
```python
from ingresskit.repair import Repairer, Schema
import boto3
import uuid

class SaaSDataImporter:
    def __init__(self):
        self.s3 = boto3.client('s3')
        self.bucket = 'saas-customer-imports'
    
    def process_customer_import(self, customer_id, file_path, schema_type):
        """Process customer CSV import with tenant isolation"""
        
        # Use customer ID as tenant for memory isolation
        repairer = Repairer(
            schema=getattr(Schema, schema_type)(),
            tenant_id=customer_id
        )
        
        # Process the file
        result = repairer.repair_file(file_path)
        
        # Generate import report
        import_id = str(uuid.uuid4())
        report = {
            "import_id": import_id,
            "customer_id": customer_id,
            "schema": schema_type,
            "rows_processed": result.summary["rows_in"],
            "rows_imported": result.summary["rows_out"],
            "success_rate": result.summary["rows_out"] / max(1, result.summary["rows_in"]),
            "sample_transformations": result.sample_diffs[:3],
            "header_mappings": result.summary["mapped_headers"]
        }
        
        # Save cleaned data to S3
        output_key = f"imports/{customer_id}/{import_id}/cleaned_data.csv"
        result.save(f"/tmp/{import_id}.csv")
        
        self.s3.upload_file(
            f"/tmp/{import_id}.csv",
            self.bucket,
            output_key
        )
        
        # Store import metadata in database
        self.save_import_metadata(report)
        
        return report
    
    def save_import_metadata(self, report):
        """Save import metadata to database"""
        # Database insertion logic here
        pass

# Usage
importer = SaaSDataImporter()

# Customer A imports contact data
report_a = importer.process_customer_import(
    customer_id="customer_123",
    file_path="customer_a_contacts.csv", 
    schema_type="contacts"
)

# Customer B imports product catalog
report_b = importer.process_customer_import(
    customer_id="customer_456",
    file_path="customer_b_products.csv",
    schema_type="products"
)
```

## Integration Patterns

### Pattern 1: Event-Driven Processing Pipeline

**Architecture:** Use IngressKit webhook processing as the first stage in an event-driven architecture.

```python
import asyncio
import aiohttp
from typing import Dict, Any

class EventPipeline:
    def __init__(self, ingresskit_url: str, api_key: str):
        self.ingresskit_url = ingresskit_url
        self.api_key = api_key
        
    async def process_webhook_event(self, source: str, payload: Dict[str, Any]):
        """Stage 1: Normalize webhook with IngressKit"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.ingresskit_url}/v1/webhooks/ingest?source={source}",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=payload
            ) as response:
                if response.status == 200:
                    canonical_event = await response.json()
                    await self.enrich_event(canonical_event)
                else:
                    await self.handle_error(source, payload, await response.text())
    
    async def enrich_event(self, event: Dict[str, Any]):
        """Stage 2: Enrich canonical event with additional data"""
        # Add customer metadata
        if event["actor"]["id"]:
            customer_data = await self.lookup_customer(event["actor"]["id"])
            event["actor"].update(customer_data)
        
        # Route to appropriate handlers
        await self.route_event(event)
    
    async def route_event(self, event: Dict[str, Any]):
        """Stage 3: Route events to appropriate handlers"""
        handlers = {
            "stripe": self.handle_payment_event,
            "github": self.handle_development_event,
            "slack": self.handle_communication_event
        }
        
        handler = handlers.get(event["source"])
        if handler:
            await handler(event)
    
    async def handle_payment_event(self, event: Dict[str, Any]):
        """Handle normalized payment events"""
        if event["action"] == "charge.succeeded":
            await self.update_customer_balance(event)
            await self.send_receipt(event)
        elif event["action"] == "charge.failed":
            await self.handle_failed_payment(event)
    
    # Additional handler methods...
```

### Pattern 2: Batch Processing with Queue Management

**Architecture:** Process large volumes of CSV imports using task queues and IngressKit.

```python
from celery import Celery
from ingresskit.repair import Repairer, Schema
import redis

app = Celery('data_processor')
redis_client = redis.Redis(host='localhost', port=6379, db=0)

@app.task
def process_csv_import(file_path: str, schema_type: str, customer_id: str):
    """Celery task for processing CSV imports"""
    try:
        # Update status
        redis_client.set(f"import_status:{customer_id}", "processing")
        
        # Process with IngressKit
        repairer = Repairer(
            schema=getattr(Schema, schema_type)(),
            tenant_id=customer_id
        )
        result = repairer.repair_file(file_path)
        
        # Save results
        output_path = f"processed/{customer_id}_{uuid.uuid4()}.csv"
        result.save(output_path)
        
        # Update status with results
        status = {
            "status": "completed",
            "rows_in": result.summary["rows_in"],
            "rows_out": result.summary["rows_out"],
            "output_file": output_path,
            "sample_diffs": result.sample_diffs
        }
        redis_client.set(f"import_status:{customer_id}", json.dumps(status))
        
        return status
        
    except Exception as e:
        error_status = {"status": "failed", "error": str(e)}
        redis_client.set(f"import_status:{customer_id}", json.dumps(error_status))
        raise

# Usage
@app.route('/import', methods=['POST'])
def start_import():
    file_path = request.json['file_path']
    schema_type = request.json['schema']
    customer_id = request.json['customer_id']
    
    # Queue the processing task
    task = process_csv_import.delay(file_path, schema_type, customer_id)
    
    return {"task_id": task.id, "status": "queued"}

@app.route('/import/status/<customer_id>')
def check_import_status(customer_id):
    status = redis_client.get(f"import_status:{customer_id}")
    if status:
        return json.loads(status)
    else:
        return {"status": "not_found"}
```

### Pattern 3: Real-time Data Validation API

**Architecture:** Create a validation service that uses IngressKit for data cleaning and validation.

```python
from flask import Flask, request, jsonify
import requests
from typing import Dict, Any, List

app = Flask(__name__)

class DataValidator:
    def __init__(self, ingresskit_url: str, api_key: str):
        self.ingresskit_url = ingresskit_url
        self.api_key = api_key
        
    def validate_contact_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean contact data"""
        # Normalize with IngressKit
        response = requests.post(
            f"{self.ingresskit_url}/v1/json/normalize?schema=contacts",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json=data
        )
        
        if response.status_code != 200:
            return {"valid": False, "errors": ["Normalization failed"]}
        
        normalized = response.json()
        
        # Additional validation rules
        errors = []
        warnings = []
        
        if not normalized["email"]:
            errors.append("Email is required")
        elif "@" not in normalized["email"]:
            errors.append("Invalid email format")
            
        if not normalized["phone"]:
            warnings.append("Phone number missing")
        elif len(normalized["phone"]) < 10:
            warnings.append("Phone number may be incomplete")
            
        if not (normalized["first_name"] or normalized["last_name"]):
            errors.append("At least first or last name required")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "normalized_data": normalized,
            "transformations": normalized["trace"]
        }

validator = DataValidator("http://localhost:8080", "your-api-key")

@app.route('/validate/contact', methods=['POST'])
def validate_contact():
    """API endpoint for contact validation"""
    data = request.json
    result = validator.validate_contact_data(data)
    
    status_code = 200 if result["valid"] else 400
    return jsonify(result), status_code

@app.route('/validate/batch', methods=['POST'])
def validate_batch():
    """Batch validation endpoint"""
    contacts = request.json.get("contacts", [])
    results = []
    
    for i, contact in enumerate(contacts):
        result = validator.validate_contact_data(contact)
        result["index"] = i
        results.append(result)
    
    summary = {
        "total": len(results),
        "valid": sum(1 for r in results if r["valid"]),
        "invalid": sum(1 for r in results if not r["valid"]),
        "results": results
    }
    
    return jsonify(summary)

# Usage examples
"""
# Single contact validation
curl -X POST http://localhost:5000/validate/contact \
  -H "Content-Type: application/json" \
  -d '{"Email": "USER@EXAMPLE.COM", "Name": "Doe, Jane"}'

# Batch validation
curl -X POST http://localhost:5000/validate/batch \
  -H "Content-Type: application/json" \
  -d '{
    "contacts": [
      {"Email": "user1@example.com", "Name": "John Smith"},
      {"Email": "invalid-email", "Name": "Jane Doe"}
    ]
  }'
"""
```

## Testing Examples

### Unit Testing SDK Components

```python
import unittest
from ingresskit.repair import Repairer, Schema
import tempfile
import csv

class TestIngressKitSDK(unittest.TestCase):
    
    def setUp(self):
        self.repairer = Repairer(Schema.contacts(), tenant_id="test")
    
    def test_contact_normalization(self):
        """Test contact data normalization"""
        # Create test CSV
        test_data = [
            ["E-Mail", "Phone Number", "Name"],
            ["USER@EXAMPLE.COM", "(555) 123-4567", "Doe, Jane"],
            ["test@domain.com", "555.987.6543", "John Smith"]
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerows(test_data)
            temp_path = f.name
        
        # Process with IngressKit
        result = self.repairer.repair_file(temp_path)
        
        # Assertions
        self.assertEqual(result.summary["rows_in"], 2)
        self.assertEqual(result.summary["rows_out"], 2)
        
        # Check first row
        first_row = result.rows_out[0]
        self.assertEqual(first_row["email"], "user@example.com")
        self.assertEqual(first_row["phone"], "5551234567")
        self.assertEqual(first_row["first_name"], "Jane")
        self.assertEqual(first_row["last_name"], "Doe")
    
    def test_unit_conversion(self):
        """Test unit conversion for products"""
        repairer = Repairer(Schema.products(), tenant_id="test")
        
        test_data = [
            ["SKU", "Name", "Weight (lb)", "Length (ft)"],
            ["ABC123", "Widget", "2.2", "1.5"]
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerows(test_data)
            temp_path = f.name
        
        result = repairer.repair_file(temp_path)
        
        # Check unit conversions
        row = result.rows_out[0]
        weight_kg = float(row["weight_kg"])
        length_m = float(row["length_m"])
        
        # 2.2 lb = 0.997903 kg (approximately)
        self.assertAlmostEqual(weight_kg, 0.997903, places=5)
        # 1.5 ft = 0.4572 m
        self.assertAlmostEqual(length_m, 0.4572, places=4)

if __name__ == '__main__':
    unittest.main()
```

### API Integration Testing

```python
import unittest
import requests
import json

class TestIngressKitAPI(unittest.TestCase):
    
    def setUp(self):
        self.base_url = "http://localhost:8080"
        self.api_key = "test-api-key"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def test_webhook_processing(self):
        """Test webhook processing endpoint"""
        stripe_payload = {
            "id": "evt_test_123",
            "type": "charge.succeeded",
            "data": {
                "object": {
                    "id": "ch_test_123",
                    "object": "charge",
                    "amount": 2500,
                    "customer": "cus_test_123"
                }
            },
            "created": 1693526400
        }
        
        response = requests.post(
            f"{self.base_url}/v1/webhooks/ingest?source=stripe",
            headers=self.headers,
            json=stripe_payload
        )
        
        self.assertEqual(response.status_code, 200)
        
        result = response.json()
        self.assertEqual(result["source"], "stripe")
        self.assertEqual(result["event_id"], "evt_test_123")
        self.assertEqual(result["action"], "charge.succeeded")
        self.assertEqual(result["subject"]["id"], "ch_test_123")
    
    def test_json_normalization(self):
        """Test JSON normalization endpoint"""
        contact_data = {
            "Email": "USER@EXAMPLE.COM",
            "Name": "Doe, Jane",
            "Phone": "(555) 123-4567"
        }
        
        response = requests.post(
            f"{self.base_url}/v1/json/normalize?schema=contacts",
            headers=self.headers,
            json=contact_data
        )
        
        self.assertEqual(response.status_code, 200)
        
        result = response.json()
        self.assertEqual(result["email"], "user@example.com")
        self.assertEqual(result["phone"], "5551234567")
        self.assertEqual(result["first_name"], "Jane")
        self.assertEqual(result["last_name"], "Doe")
    
    def test_credit_balance(self):
        """Test credit balance endpoint"""
        response = requests.get(
            f"{self.base_url}/v1/billing/balance",
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        self.assertEqual(response.status_code, 200)
        
        result = response.json()
        self.assertIn("balance", result)
        self.assertIn("api_key", result)

if __name__ == '__main__':
    unittest.main()
```

---

*These examples demonstrate the versatility and power of IngressKit for various data ingestion scenarios. For production deployments, see the Deployment Guide.*
