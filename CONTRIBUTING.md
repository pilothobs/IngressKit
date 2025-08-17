# Contributing to IngressKit

Thank you for your interest in contributing to IngressKit! We welcome contributions from the community and are excited to see what you'll build.

## 🎯 **Ways to Contribute**

### 🔧 **Add New Schemas**
The most valuable contributions are new schemas for different industries and use cases.

### 🐛 **Bug Fixes & Performance**
Found an issue? Performance bottleneck? We'd love your help fixing it.

### 📚 **Documentation & Examples**
Help other developers by improving docs or adding real-world examples.

### 🧪 **Test Cases**
Edge cases, unusual data formats, stress tests - all welcome.

### 🌐 **Webhook Sources**
Add support for new webhook providers (Shopify, Mailchimp, etc.).

## 🚀 **Getting Started**

### 1. Fork & Clone
```bash
git clone https://github.com/your-username/ingresskit.git
cd ingresskit
```

### 2. Set Up Development Environment
```bash
# SDK development
cd sdk/python
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .  # Install in development mode

# Server development
cd ../../server
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Run Tests
```bash
# SDK tests
cd sdk/python
python -m pytest

# Server tests
cd ../../server
python -m pytest tests/
```

### 4. Make Your Changes
Follow the guidelines below for your specific contribution type.

### 5. Submit Pull Request
- Create a descriptive branch name (`add-healthcare-schema`, `fix-date-parsing`)
- Write clear commit messages
- Include tests for new functionality
- Update documentation as needed

## 📋 **Adding New Schemas**

Schemas are the heart of IngressKit. Here's how to add a new one:

### Schema Template

```python
# In sdk/python/ingresskit/repair.py

# 1. Add your schema to CANONICAL_SCHEMAS
CANONICAL_SCHEMAS: Dict[str, List[str]] = {
    "contacts": ["email", "phone", "first_name", "last_name", "company"],
    "transactions": ["id", "amount", "currency", "occurred_at", "customer_id"],
    "products": ["sku", "name", "price", "currency", "category", "weight_kg", "length_m"],
    # Add your new schema here
    "your_schema": ["field1", "field2", "field3", "field4"],
}

# 2. Add field synonyms to HEADER_SYNONYMS
HEADER_SYNONYMS: Dict[str, List[str]] = {
    # ... existing synonyms ...
    
    # Your schema synonyms
    "field1": ["field1", "f1", "primary_field", "main_field"],
    "field2": ["field2", "f2", "secondary_field", "alt_field"],
    "field3": ["field3", "f3", "third_field"],
    "field4": ["field4", "f4", "fourth_field"],
}

# 3. Add coercion logic to _coerce_value() if needed
def _coerce_value(field: str, value: str) -> Tuple[Optional[str], Optional[str]]:
    # ... existing logic ...
    
    if field in {"your_special_field"}:
        # Custom transformation logic
        return transform_your_field(value), None
    
    # ... rest of function ...

# 4. Add schema factory method to Schema class
class Schema:
    # ... existing methods ...
    
    @staticmethod
    def your_schema() -> List[str]:
        return CANONICAL_SCHEMAS["your_schema"]
```

### Schema Contribution Checklist

- [ ] **Clear Use Case**: Describe what industry/problem this schema solves
- [ ] **Field Documentation**: Document what each field represents
- [ ] **Synonyms**: Include common variations of field names
- [ ] **Test Data**: Provide sample messy/clean CSV files
- [ ] **Coercion Logic**: Add custom transformation logic if needed
- [ ] **Tests**: Write tests for your schema
- [ ] **Documentation**: Update README and docs with your schema

### Example: Healthcare Schema Contribution

```python
# Use Case: Medical record imports from various EMR systems
CANONICAL_SCHEMAS["healthcare"] = [
    "patient_id", "first_name", "last_name", "date_of_birth", 
    "gender", "phone", "email", "diagnosis_code", "visit_date"
]

HEADER_SYNONYMS.update({
    "patient_id": ["patient_id", "patient id", "mrn", "medical record number", "id"],
    "date_of_birth": ["dob", "date of birth", "birth date", "birthdate", "born"],
    "gender": ["gender", "sex", "m/f"],
    "diagnosis_code": ["dx", "diagnosis", "icd10", "icd-10", "diagnosis code"],
    "visit_date": ["visit date", "appointment date", "seen on", "date seen"],
})

# Custom coercion for medical data
def _coerce_healthcare_fields(field: str, value: str):
    if field == "gender":
        v = value.lower().strip()
        if v in ["m", "male", "man"]: return "M", None
        if v in ["f", "female", "woman"]: return "F", None
        return None, f"invalid_gender:{value}"
    
    if field == "diagnosis_code":
        # Normalize ICD-10 codes
        code = re.sub(r"[^A-Z0-9.]", "", value.upper())
        return code if len(code) >= 3 else None, None
```

## 🌐 **Adding Webhook Sources**

### Webhook Source Template

```python
# In server/main_oss.py (or main.py)

def normalize_your_service_webhook(payload: Dict[str, Any]) -> CanonicalEvent:
    """Convert YourService webhook to canonical event format"""
    
    # Extract key data from payload
    event_data = payload.get("data", {})
    user_info = payload.get("user", {})
    
    trace = [{"op": "your_service_normalize", "timestamp": datetime.now(timezone.utc).isoformat()}]
    
    return CanonicalEvent(
        event_id=str(payload.get("id", "")),
        source="your_service",
        occurred_at=_utc_timestamp(payload.get("timestamp")),
        actor={
            "id": user_info.get("id"),
            "email": user_info.get("email")
        } if user_info else None,
        subject={
            "type": event_data.get("type", "unknown"),
            "id": event_data.get("id")
        },
        action=str(payload.get("event_type", "unknown")),
        metadata={k: v for k, v in event_data.items() if k not in {"id", "type"}},
        trace=trace
    )

# Add to webhook router
@app.post("/v1/webhooks/normalize", response_model=CanonicalEvent)
async def normalize_webhook(request: Request, source: str):
    # ... existing code ...
    
    elif source == "your_service":
        return normalize_your_service_webhook(payload)
    
    # ... rest of function ...
```

### Webhook Contribution Requirements

- [ ] **Service Documentation**: Link to official webhook docs
- [ ] **Sample Payloads**: Include real example webhooks (anonymized)
- [ ] **Event Types**: Document which event types are supported
- [ ] **Field Mapping**: Explain how fields map to canonical format
- [ ] **Tests**: Add test fixtures and test cases
- [ ] **Error Handling**: Handle malformed/missing fields gracefully

## 🧪 **Writing Tests**

### SDK Tests
```python
# In sdk/python/tests/test_your_schema.py
import unittest
from ingresskit.repair import Repairer, Schema
import tempfile
import csv

class TestYourSchema(unittest.TestCase):
    
    def setUp(self):
        self.repairer = Repairer(Schema.your_schema(), tenant_id="test")
    
    def test_your_schema_normalization(self):
        """Test your schema with sample data"""
        test_data = [
            ["Field1", "Field2", "Field3"],
            ["value1", "value2", "value3"],
            ["value4", "value5", "value6"]
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerows(test_data)
            temp_path = f.name
        
        result = self.repairer.repair_file(temp_path)
        
        # Assertions
        self.assertEqual(result.summary["rows_in"], 2)
        self.assertEqual(result.summary["rows_out"], 2)
        
        # Check specific transformations
        first_row = result.rows_out[0]
        self.assertEqual(first_row["field1"], "expected_value1")
```

### Server Tests
```python
# In server/tests/test_your_webhook.py
import unittest
from fastapi.testclient import TestClient
from main_oss import app

class TestYourWebhook(unittest.TestCase):
    
    def setUp(self):
        self.client = TestClient(app)
    
    def test_your_service_webhook(self):
        """Test your service webhook normalization"""
        payload = {
            "id": "evt_123",
            "event_type": "user.created",
            "data": {"id": "user_456", "email": "test@example.com"},
            "timestamp": 1693526400
        }
        
        response = self.client.post(
            "/v1/webhooks/normalize?source=your_service",
            json=payload
        )
        
        self.assertEqual(response.status_code, 200)
        
        result = response.json()
        self.assertEqual(result["source"], "your_service")
        self.assertEqual(result["event_id"], "evt_123")
        self.assertEqual(result["action"], "user.created")
```

## 📚 **Documentation Standards**

### Code Documentation
- Use clear, descriptive function/variable names
- Add docstrings for all public functions
- Comment complex logic or business rules
- Include type hints where possible

### README Updates
When adding new schemas or features:
- Update the "Built-in Schemas" section
- Add examples to the "Quick Start" section
- Update performance numbers if applicable
- Add to the roadmap if it's a major feature

### Example Documentation
For new schemas, add to `examples/` directory:
- `your_schema_messy.csv` - Sample messy input
- `your_schema_clean.csv` - Expected clean output
- `your_schema_example.py` - Usage example

## 🎮 **IngressKit Data Challenge**

### Submitting Challenging Data
Have a CSV that breaks IngressKit? We love challenges!

1. **Anonymize Your Data**: Remove sensitive information
2. **Create GitHub Discussion**: Use the "Data Challenge" category
3. **Describe the Challenge**: What makes this CSV difficult?
4. **Expected Outcome**: What should the clean version look like?

### Challenge Guidelines
- Data must be anonymized/synthetic
- Provide context about the data source
- Explain why existing schemas don't work
- Be willing to collaborate on the solution

## 🏷️ **Pull Request Guidelines**

### Branch Naming
- `feature/schema-healthcare` - New schema
- `feature/webhook-shopify` - New webhook source
- `fix/date-parsing-bug` - Bug fix
- `docs/api-examples` - Documentation update

### Commit Messages
Use conventional commit format:
```
feat(schema): add healthcare schema for EMR data

- Adds patient_id, diagnosis_code, visit_date fields
- Includes gender normalization (M/F)
- Handles ICD-10 code formatting
- Closes #123
```

### PR Description Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] New schema
- [ ] New webhook source  
- [ ] Bug fix
- [ ] Performance improvement
- [ ] Documentation update

## Testing
- [ ] Added tests for new functionality
- [ ] All existing tests pass
- [ ] Manual testing completed

## Documentation
- [ ] Updated README if needed
- [ ] Added example files
- [ ] Updated API docs if needed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Added tests that prove fix/feature works
- [ ] New/updated documentation is clear
```

## 🤝 **Community Guidelines**

### Code of Conduct
- Be respectful and inclusive
- Help newcomers learn and contribute
- Provide constructive feedback
- Focus on what's best for the community

### Getting Help
- 💬 **GitHub Discussions**: For questions and ideas
- 🐛 **GitHub Issues**: For bugs and feature requests
- 📧 **Email**: For sensitive issues

### Recognition
Contributors are recognized in:
- Release notes
- README contributors section
- GitHub contributor graphs
- Special mentions for major contributions

## 🎯 **Priority Contributions**

We're especially looking for:

### High Priority
- **Healthcare schema** (EMR, patient data)
- **Financial schema** (banking, trading data)
- **Shopify webhooks** (e-commerce events)
- **Mailchimp webhooks** (marketing events)

### Medium Priority
- **Real estate schema** (property listings)
- **Education schema** (student records)
- **Inventory schema** (warehouse management)
- **Performance optimizations**

### Nice to Have
- **Custom validation rules**
- **Plugin architecture**
- **GraphQL API**
- **Streaming data support**

## 📞 **Questions?**

Don't hesitate to reach out:
- 💬 [GitHub Discussions](https://github.com/pilothobs/ingresskit/discussions)
- 📧 [Email the maintainer](mailto:contribute@pilothobs.com)
- 🐛 [Open an issue](https://github.com/pilothobs/ingresskit/issues/new)

---

**Thanks for contributing to IngressKit! Every contribution makes data ingestion easier for developers everywhere.** 🚀
