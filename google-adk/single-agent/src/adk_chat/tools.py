"""A custom function tool for the agent."""

from __future__ import annotations

UNITS = ("C", "F", "K")


def convert(value: float, from_unit: str, to_unit: str) -> float:
    """Convert a temperature between Celsius, Fahrenheit and Kelvin."""
    source, target = from_unit.strip().upper(), to_unit.strip().upper()
    for unit in (source, target):
        if unit not in UNITS:
            raise ValueError(f"unknown unit {unit!r}; expected one of {UNITS}")
    celsius = {"C": value, "F": (value - 32) * 5 / 9, "K": value - 273.15}[source]
    return {"C": celsius, "F": celsius * 9 / 5 + 32, "K": celsius + 273.15}[target]


def convert_temperature(value: float, from_unit: str, to_unit: str) -> dict[str, str]:
    """Convert a temperature between C (Celsius), F (Fahrenheit) and K (Kelvin).

    Args:
        value: The temperature to convert.
        from_unit: The unit of `value`: C, F or K.
        to_unit: The unit to convert to: C, F or K.

    Returns:
        {"status": "success", "result": "<value> <unit>"}, or
        {"status": "error", "error": "<message>"} for an unknown unit.
    """
    try:
        result = convert(value, from_unit, to_unit)
    except ValueError as e:
        return {"status": "error", "error": str(e)}
    return {"status": "success", "result": f"{result:.2f} {to_unit.strip().upper()}"}
