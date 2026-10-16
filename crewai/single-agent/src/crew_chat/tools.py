"""A custom tool for the agent. No Kynomesh imports."""

from __future__ import annotations

from crewai.tools import tool

UNITS = ("C", "F", "K")


def convert(value: float, from_unit: str, to_unit: str) -> float:
    """Convert a temperature between Celsius, Fahrenheit and Kelvin."""
    source, target = from_unit.strip().upper(), to_unit.strip().upper()
    for unit in (source, target):
        if unit not in UNITS:
            raise ValueError(f"unknown unit {unit!r}; expected one of {UNITS}")
    celsius = {"C": value, "F": (value - 32) * 5 / 9, "K": value - 273.15}[source]
    return {"C": celsius, "F": celsius * 9 / 5 + 32, "K": celsius + 273.15}[target]


@tool("convert_temperature")
def convert_temperature(value: float, from_unit: str, to_unit: str) -> str:
    """Convert a temperature between C (Celsius), F (Fahrenheit) and K (Kelvin)."""
    try:
        return f"{convert(value, from_unit, to_unit):.2f} {to_unit.strip().upper()}"
    except ValueError as e:
        return f"Error: {e}"
