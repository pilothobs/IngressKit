from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
import csv
import json
from pathlib import Path
from collections import OrderedDict
from dateutil import parser as date_parser
from .units import normalize_mass, normalize_length
import re
import datetime as dt


CANONICAL_SCHEMAS: Dict[str, List[str]] = {
    "contacts": ["email", "phone", "first_name", "last_name", "company"],
    "transactions": ["id", "amount", "currency", "occurred_at", "customer_id"],
    # Extended with canonical unit fields for demonstration
    "products": ["sku", "name", "price", "currency", "category", "weight_kg", "length_m"],
}


HEADER_SYNONYMS: Dict[str, List[str]] = {
    "email": ["email", "e-mail", "mail", "email address"],
    "phone": ["phone", "phone number", "tel", "telephone"],
    "first_name": ["first", "first name", "fname", "given name"],
    "last_name": ["last", "last name", "lname", "surname", "family name"],
    "company": ["company", "organization", "org", "employer"],
    # transactions
    "id": ["id", "txn id", "transaction id"],
    "amount": ["amount", "total", "value", "amount_cents", "amount (usd)", "price"],
    "currency": ["currency", "curr", "iso currency"],
    "occurred_at": ["date", "occurred at", "timestamp", "created", "time"],
    "customer_id": ["customer id", "customer", "client id", "account id"],
    # products
    "sku": ["sku", "id", "product id", "code"],
    "name": ["name", "title", "product name"],
    "price": ["price", "amount", "cost"],
    "category": ["category", "type", "group"],
    "weight_kg": ["weight", "mass", "weight_kg"],
    "length_m": ["length", "size", "height", "width", "depth", "length_m"],
}


def _slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    s = re.sub(r"\s+", "_", s)
    return s


def _guess_header(name: str, schema: List[str]) -> Optional[str]:
    slug = _slugify(name)
    # Exact
    if slug in schema:
        return slug
    # Synonyms
    for canonical, syns in HEADER_SYNONYMS.items():
        if canonical in schema and slug in {_slugify(x) for x in syns}:
            return canonical
    # Handle unit-bearing headers like "Weight (lb)" or "Length (ft)"
    m = re.match(r"^(.+?)\s*\(([^)]+)\)\s*$", name.strip())
    if m:
        base, unit = m.group(1), m.group(2)
        base_slug = _slugify(base)
        # Map base to a canonical unit field if present in schema via synonyms
        for canonical, syns in HEADER_SYNONYMS.items():
            if canonical in schema and base_slug in {_slugify(x) for x in syns}:
                # Return canonical field; unit will be handled during coercion
                return canonical
    return None


def _coerce_value(field: str, value: str) -> Tuple[Optional[str], Optional[str]]:
    if value is None:
        return None, None
    v = value.strip()
    if v == "":
        return None, None
    try:
        if field in {"email"}:
            return v.lower(), None
        if field in {"phone"}:
            digits = re.sub(r"\D", "", v)
            return digits, None
        if field in {"amount", "price"}:
            num = re.sub(r"[^0-9.\-]", "", v)
            return f"{float(num):.2f}", None
        if field in {"occurred_at"}:
            # Try common fast paths first
            for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d", "%d-%b-%Y", "%d/%m/%Y", "%b %d, %Y"):
                try:
                    return dt.datetime.strptime(v, fmt).date().isoformat(), None
                except Exception:
                    pass
            # Fallback to dateutil parser
            try:
                return date_parser.parse(v).date().isoformat(), None
            except Exception:
                return None, f"unrecognized_date:{v}"
        if field in {"currency"}:
            cur = re.sub(r"[^A-Za-z]", "", v).upper()
            COMMON = {"USD", "EUR", "GBP", "JPY", "CAD", "AUD", "INR"}
            if cur in COMMON:
                return cur, None
            if 2 <= len(cur) <= 4:
                return cur, None
            return None, f"bad_currency:{v}"
        if field in {"id", "customer_id", "sku"}:
            return v, None
        if field in {"name", "category"}:
            return v.strip(), None
        return v, None
    except Exception as e:
        return None, f"coerce_error:{type(e).__name__}"


def _extract_header_unit(header: str) -> Optional[str]:
    m = re.match(r"^(.+?)\s*\(([^)]+)\)\s*$", header.strip())
    if m:
        return m.group(2).strip()
    return None


@dataclass
class RepairResult:
    rows_out: List[Dict[str, Optional[str]]]
    summary: Dict[str, Any]
    sample_diffs: List[Dict[str, Any]]

    def save(self, path: str | Path) -> None:
        path = Path(path)
        fieldnames = self.summary.get("schema", [])
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in self.rows_out:
                writer.writerow({k: ("" if v is None else v) for k, v in r.items()})


class Schema:
    @staticmethod
    def contacts() -> List[str]:
        return CANONICAL_SCHEMAS["contacts"]

    @staticmethod
    def transactions() -> List[str]:
        return CANONICAL_SCHEMAS["transactions"]

    @staticmethod
    def products() -> List[str]:
        return CANONICAL_SCHEMAS["products"]


class Repairer:
    def __init__(self, schema: List[str], tenant_id: Optional[str] = None):
        self.schema = schema
        self.tenant_id = tenant_id or "default"

    def repair_file(self, path: str | Path) -> RepairResult:
        path = Path(path)
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            rows = list(reader)

        if not rows:
            return RepairResult([], {"schema": self.schema, "rows_in": 0, "rows_out": 0}, [])

        raw_headers = rows[0]
        mapped = []
        header_map: Dict[int, Optional[str]] = {}
        for i, h in enumerate(raw_headers):
            header_map[i] = _guess_header(h, self.schema)

        # Build output rows
        out_rows: List[Dict[str, Optional[str]]] = []
        sample_diffs: List[Dict[str, Any]] = []

        for r in rows[1:]:
            out: Dict[str, Optional[str]] = {k: None for k in self.schema}
            before: Dict[str, Any] = {}
            after: Dict[str, Any] = {}
            for i, val in enumerate(r):
                target = header_map.get(i)
                if target is None:
                    continue
                before[target] = val
                coerced, err = _coerce_value(target, val)
                out[target] = coerced
                after[target] = coerced
                # errors could be collected if desired
                # Unit-aware handling for products: if header had units, convert to canonical
                if target in {"weight_kg", "length_m"}:
                    unit = _extract_header_unit(raw_headers[i] or "")
                    if unit:
                        try:
                            num = float(re.sub(r"[^0-9.\-]", "", val))
                        except Exception:
                            num = None
                        if num is not None:
                            if target == "weight_kg":
                                kg, _ = normalize_mass(num, unit)
                                out[target] = None if kg is None else f"{kg:.6f}"
                                after[target] = out[target]
                            elif target == "length_m":
                                m, _ = normalize_length(num, unit)
                                out[target] = None if m is None else f"{m:.6f}"
                                after[target] = out[target]
            out_rows.append(out)
            if len(sample_diffs) < 5:
                sample_diffs.append({"before": before, "after": after})

        summary = {
            "schema": self.schema,
            "rows_in": max(0, len(rows) - 1),
            "rows_out": len(out_rows),
            "mapped_headers": {i: header_map[i] for i in range(len(raw_headers))},
        }

        return RepairResult(out_rows, summary, sample_diffs)


