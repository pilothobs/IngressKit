# IngressKit Python SDK Reference

## Overview

The IngressKit Python SDK provides a powerful, deterministic CSV/Excel repair system that transforms messy data files into clean, schema-compliant formats. It includes intelligent header mapping, type coercion, unit conversion, and comprehensive audit trails.

## Installation

### From Source
```bash
cd sdk/python
pip install -r requirements.txt
```

### Development Installation
```bash
cd sdk/python
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Quick Start

### Command Line Interface
```bash
# Basic usage
python -m ingresskit.cli --in messy_contacts.csv --out clean_contacts.csv --schema contacts

# With custom tenant
python -m ingresskit.cli --in data.csv --out clean.csv --schema transactions --tenant-id company_123
```

### Programmatic Usage
```python
from ingresskit.repair import Repairer, Schema
from pathlib import Path

# Initialize repairer
repairer = Repairer(schema=Schema.contacts(), tenant_id="my_company")

# Process file
result = repairer.repair_file("messy_data.csv")

# Save cleaned data
result.save("clean_data.csv")

# Inspect results
print(f"Processed {result.summary['rows_in']} → {result.summary['rows_out']} rows")
print("Sample transformations:", result.sample_diffs)
```

## Core Classes

### `Repairer`

The main class for processing CSV/Excel files and applying schema-based transformations.

#### Constructor
```python
Repairer(schema: List[str], tenant_id: Optional[str] = None)
```

**Parameters:**
- `schema`: List of canonical field names (use `Schema` class helpers)
- `tenant_id`: Optional tenant identifier for episodic memory (future feature)

**Example:**
```python
repairer = Repairer(
    schema=Schema.contacts(),
    tenant_id="customer_123"
)
```

#### Methods

##### `repair_file(path: str | Path) -> RepairResult`

Processes a CSV file and returns cleaned, normalized data.

**Parameters:**
- `path`: Path to input CSV file

**Returns:**
- `RepairResult` object with cleaned data, summary, and transformation logs

**Example:**
```python
result = repairer.repair_file("input.csv")
print(f"Rows processed: {result.summary['rows_in']} → {result.summary['rows_out']}")
```

### `RepairResult`

Container for processed data and metadata.

#### Attributes
- `rows_out`: List of cleaned data dictionaries
- `summary`: Processing metadata and statistics
- `sample_diffs`: Sample of before/after transformations

#### Methods

##### `save(path: str | Path) -> None`

Saves cleaned data to CSV file.

**Parameters:**
- `path`: Output file path

**Example:**
```python
result.save("cleaned_output.csv")
```

### `Schema`

Static factory class for predefined schemas.

#### Available Schemas

##### `Schema.contacts() -> List[str]`
Returns: `["email", "phone", "first_name", "last_name", "company"]`

**Use case:** Customer contact lists, lead imports, CRM data

##### `Schema.transactions() -> List[str]`
Returns: `["id", "amount", "currency", "occurred_at", "customer_id"]`

**Use case:** Payment records, financial transactions, billing data

##### `Schema.products() -> List[str]`
Returns: `["sku", "name", "price", "currency", "category", "weight_kg", "length_m"]`

**Use case:** Product catalogs, inventory data, e-commerce listings

## Field Mapping & Synonyms

The SDK automatically maps messy headers to canonical field names using intelligent synonym matching.

### Header Synonyms

#### Contacts Schema
| Canonical Field | Recognized Synonyms |
|----------------|-------------------|
| `email` | email, e-mail, mail, email address |
| `phone` | phone, phone number, tel, telephone |
| `first_name` | first, first name, fname, given name |
| `last_name` | last, last name, lname, surname, family name |
| `company` | company, organization, org, employer |

#### Transactions Schema
| Canonical Field | Recognized Synonyms |
|----------------|-------------------|
| `id` | id, txn id, transaction id |
| `amount` | amount, total, value, amount_cents, amount (usd), price |
| `currency` | currency, curr, iso currency |
| `occurred_at` | date, occurred at, timestamp, created, time |
| `customer_id` | customer id, customer, client id, account id |

#### Products Schema
| Canonical Field | Recognized Synonyms |
|----------------|-------------------|
| `sku` | sku, id, product id, code |
| `name` | name, title, product name |
| `price` | price, amount, cost |
| `category` | category, type, group |
| `weight_kg` | weight, mass, weight_kg |
| `length_m` | length, size, height, width, depth, length_m |

### Unit-Aware Headers

The SDK automatically detects and converts units in headers like:
- `Weight (lb)` → converts to kg
- `Length (ft)` → converts to meters
- `Height (in)` → converts to meters

## Data Transformations

### Type Coercion Rules

#### Email Fields
- Converted to lowercase
- Trimmed of whitespace
- Preserved as-is for validation downstream

#### Phone Fields
- All non-digit characters removed
- Returns digits-only string
- Handles formats: `(555) 123-4567`, `555.123.4567`, `+1-555-123-4567`

#### Monetary Fields (`amount`, `price`)
- Removes currency symbols and formatting
- Converts to float with 2 decimal places
- Handles: `$1,234.56`, `1234.56 USD`, `€1.234,56`

#### Date Fields (`occurred_at`)
- Multiple format recognition
- Fast-path common formats: `YYYY-MM-DD`, `MM/DD/YYYY`, `DD/MM/YYYY`
- Fallback to dateutil parser for complex formats
- Output: ISO date format (`YYYY-MM-DD`)

#### Currency Fields
- Extracts alphabetic currency codes
- Validates against common currencies (USD, EUR, GBP, etc.)
- Converts to uppercase
- Returns 2-4 character codes

#### Unit Conversions

##### Mass Conversion (`weight_kg`)
Supported units:
- `kg`, `kilogram`, `kilograms` (base unit)
- `g`, `gram`, `grams` (×0.001)
- `lb`, `lbs`, `pound`, `pounds` (×0.45359237)

##### Length Conversion (`length_m`)
Supported units:
- `m`, `meter`, `meters` (base unit)
- `km`, `kilometer`, `kilometers` (×1000)
- `ft`, `feet` (×0.3048)
- `in`, `inch` (×0.0254)

## Error Handling

### Graceful Degradation
- Invalid values become `None` rather than causing failures
- Error details captured in transformation logs
- Processing continues even with malformed data

### Error Types
- `unrecognized_date:value` - Date parsing failed
- `bad_currency:value` - Currency code invalid
- `coerce_error:ExceptionType` - General coercion failure
- `unknown_length_unit:unit` - Unsupported length unit
- `unknown_mass_unit:unit` - Unsupported mass unit

## Advanced Usage

### Custom Processing Pipeline
```python
from ingresskit.repair import Repairer, Schema, RepairResult
import json

# Initialize repairer
repairer = Repairer(Schema.contacts())

# Process multiple files
results = []
for file_path in ["contacts1.csv", "contacts2.csv", "contacts3.csv"]:
    result = repairer.repair_file(file_path)
    results.append(result)
    
    # Log processing stats
    print(f"{file_path}: {result.summary['rows_in']} → {result.summary['rows_out']} rows")

# Combine all cleaned data
all_clean_rows = []
for result in results:
    all_clean_rows.extend(result.rows_out)

# Save combined dataset
combined_result = RepairResult(
    rows_out=all_clean_rows,
    summary={"schema": Schema.contacts(), "total_files": len(results)},
    sample_diffs=[]
)
combined_result.save("combined_contacts.csv")
```

### Inspecting Transformations
```python
result = repairer.repair_file("messy_data.csv")

# View header mappings
print("Header Mappings:")
for col_idx, canonical in result.summary["mapped_headers"].items():
    print(f"  Column {col_idx}: {canonical}")

# View sample transformations
print("\nSample Transformations:")
for i, diff in enumerate(result.sample_diffs):
    print(f"Row {i+1}:")
    print(f"  Before: {diff['before']}")
    print(f"  After:  {diff['after']}")
```

### Working with Results Data
```python
result = repairer.repair_file("products.csv")

# Access cleaned data
for row in result.rows_out:
    if row["weight_kg"]:
        weight = float(row["weight_kg"])
        print(f"Product {row['sku']}: {weight} kg")

# Filter and process
expensive_products = [
    row for row in result.rows_out 
    if row["price"] and float(row["price"]) > 100.0
]
```

## CLI Reference

### Command Syntax
```bash
python -m ingresskit.cli [OPTIONS]
```

### Options
- `--in PATH` (required): Input CSV file path
- `--out PATH` (required): Output CSV file path  
- `--schema TEXT`: Target schema (contacts|transactions|products) [default: contacts]
- `--tenant-id TEXT`: Tenant identifier [default: default]

### Examples
```bash
# Process contact data
python -m ingresskit.cli --in leads.csv --out clean_leads.csv --schema contacts

# Process transaction data with tenant
python -m ingresskit.cli --in payments.csv --out clean_payments.csv --schema transactions --tenant-id acme_corp

# Process product catalog
python -m ingresskit.cli --in inventory.csv --out clean_inventory.csv --schema products
```

## Best Practices

### 1. Schema Selection
Choose the schema that best matches your data structure:
- **contacts**: For people/customer data
- **transactions**: For financial/payment data  
- **products**: For inventory/catalog data

### 2. Data Quality
- Review `sample_diffs` to understand transformations
- Check `summary` statistics for data loss indicators
- Validate critical fields in output data

### 3. Performance
- Process files in reasonable batches (< 100MB recommended)
- Use appropriate tenant IDs for multi-tenant scenarios
- Monitor memory usage for very large files

### 4. Error Recovery
- Always check for `None` values in critical fields
- Implement fallback logic for failed transformations
- Log transformation errors for manual review

## Integration Examples

### With Pandas
```python
import pandas as pd
from ingresskit.repair import Repairer, Schema

# Process with IngressKit
repairer = Repairer(Schema.contacts())
result = repairer.repair_file("messy_contacts.csv")

# Convert to DataFrame
df = pd.DataFrame(result.rows_out)

# Continue with pandas processing
df['email'].fillna('no-email@example.com', inplace=True)
df.to_csv("final_contacts.csv", index=False)
```

### With Database Loading
```python
import sqlite3
from ingresskit.repair import Repairer, Schema

# Process data
repairer = Repairer(Schema.transactions())
result = repairer.repair_file("transactions.csv")

# Load into database
conn = sqlite3.connect("data.db")
cursor = conn.cursor()

for row in result.rows_out:
    cursor.execute("""
        INSERT INTO transactions (id, amount, currency, occurred_at, customer_id)
        VALUES (?, ?, ?, ?, ?)
    """, (row["id"], row["amount"], row["currency"], row["occurred_at"], row["customer_id"]))

conn.commit()
conn.close()
```

## Troubleshooting

### Common Issues

#### 1. Empty Output File
**Problem**: All rows are filtered out during processing
**Solution**: Check input data format and schema compatibility

#### 2. Header Mapping Failures
**Problem**: Important columns not recognized
**Solution**: Review synonym lists, consider custom mapping

#### 3. Unit Conversion Errors
**Problem**: Units not recognized in headers
**Solution**: Verify unit format matches supported units list

#### 4. Date Parsing Issues
**Problem**: Dates not converted properly
**Solution**: Check date formats, consider preprocessing

### Debug Mode
```python
# Enable verbose processing
result = repairer.repair_file("data.csv")

# Inspect all transformations
for i, row in enumerate(result.rows_out):
    if i < len(result.sample_diffs):
        print(f"Row {i}: {result.sample_diffs[i]}")
```

## Extending the SDK

### Adding Custom Schemas
```python
# Define new schema
CUSTOM_SCHEMA = ["field1", "field2", "field3"]

# Add synonyms
HEADER_SYNONYMS.update({
    "field1": ["field1", "f1", "first_field"],
    "field2": ["field2", "f2", "second_field"],
})

# Use custom schema
repairer = Repairer(schema=CUSTOM_SCHEMA)
```

### Custom Coercion Logic
Extend `_coerce_value()` function for custom field types:

```python
def custom_coerce_value(field: str, value: str):
    if field == "custom_field":
        # Custom transformation logic
        return transform_custom(value), None
    return _coerce_value(field, value)  # Fallback to default
```

---

*For more examples and advanced usage patterns, see the `examples/` directory and server integration documentation.*
