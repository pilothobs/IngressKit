from typing import Tuple, Optional


LENGTH_UNITS = {
    "m": 1.0,
    "meter": 1.0,
    "meters": 1.0,
    "km": 1000.0,
    "kilometer": 1000.0,
    "kilometers": 1000.0,
    "ft": 0.3048,
    "feet": 0.3048,
    "inch": 0.0254,
    "in": 0.0254,
}


MASS_UNITS = {
    "kg": 1.0,
    "kilogram": 1.0,
    "kilograms": 1.0,
    "g": 0.001,
    "gram": 0.001,
    "grams": 0.001,
    "lb": 0.45359237,
    "lbs": 0.45359237,
    "pound": 0.45359237,
    "pounds": 0.45359237,
}


def normalize_length(value: float, unit: str) -> Tuple[Optional[float], Optional[str]]:
    u = unit.strip().lower()
    if u in LENGTH_UNITS:
        return value * LENGTH_UNITS[u], None
    return None, f"unknown_length_unit:{unit}"


def normalize_mass(value: float, unit: str) -> Tuple[Optional[float], Optional[str]]:
    u = unit.strip().lower()
    if u in MASS_UNITS:
        return value * MASS_UNITS[u], None
    return None, f"unknown_mass_unit:{unit}"


