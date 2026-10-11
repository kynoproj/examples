"""An in-process custom tool for the agent. No Kynomesh imports."""

from __future__ import annotations

from typing import Any

from claude_agent_sdk import tool

UNITS = ("C", "F", "K")


def convert(value: float, from_unit: str, to_unit: str) -> float:
    """Convert a temperature between Celsius, Fahrenheit and Kelvin."""
    source, target = from_unit.strip().upper(), to_unit.strip().upper()
    for unit in (source, target):
        if unit not in UNITS:
            raise ValueError(f"unknown unit {unit!r}; expected one of {UNITS}")
    celsius = {"C": value, "F": (value - 32) * 5 / 9, "K": value - 273.15}[source]
    return {"C": celsius, "F": celsius * 9 / 5 + 32, "K": celsius + 273.15}[target]


@tool(
    "convert_temperature",
    "Convert a temperature between C (Celsius), F (Fahrenheit) and K (Kelvin).",
    {"value": float, "from_unit": str, "to_unit": str},
)
async def convert_temperature(args: dict[str, Any]) -> dict[str, Any]:
    try:
        result = convert(args["value"], args["from_unit"], args["to_unit"])
    except (KeyError, ValueError) as e:
        return {"content": [{"type": "text", "text": f"Error: {e}"}], "is_error": True}
    return {"content": [{"type": "text", "text": f"{result:.2f} {args['to_unit'].strip().upper()}"}]}
