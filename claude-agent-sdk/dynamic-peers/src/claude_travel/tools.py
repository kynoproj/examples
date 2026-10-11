"""Worker tools: deterministic stubs over small built-in data. No Kynomesh imports."""

from __future__ import annotations

from typing import Any

from claude_agent_sdk import tool

_FLIGHTS: dict[str, tuple[str, ...]] = {
    "tokyo": ("NH7 08:50 -> 13:10+1, $1,120", "UA837 11:40 -> 15:55+1, $980"),
    "paris": ("AF83 17:05 -> 12:55+1, $870", "UA990 16:30 -> 12:20+1, $810"),
    "lisbon": ("TP238 15:20 -> 10:05+1, $740",),
}
_HOTELS: dict[str, tuple[str, ...]] = {
    "tokyo": ("Shinjuku Granbell, $140/night", "Park Hyatt Tokyo, $520/night"),
    "paris": ("Hotel du Louvre, $310/night", "Ibis Paris Bastille, $120/night"),
    "lisbon": ("Memmo Alfama, $210/night",),
}
_FORECASTS: dict[str, str] = {
    "tokyo": "Sat: sunny, 22C. Sun: light rain, 19C.",
    "paris": "Sat: cloudy, 16C. Sun: sunny, 18C.",
    "lisbon": "Sat: sunny, 24C. Sun: sunny, 25C.",
}


def flights_report(origin: str, destination: str) -> str:
    options = _FLIGHTS.get(destination.strip().lower())
    if not options:
        return f"No flights found to {destination!r}."
    return f"Flights {origin} -> {destination}:\n" + "\n".join(options)


def hotels_report(city: str) -> str:
    options = _HOTELS.get(city.strip().lower())
    if not options:
        return f"No hotels found in {city!r}."
    return f"Hotels in {city}:\n" + "\n".join(options)


def forecast_report(city: str) -> str:
    return _FORECASTS.get(city.strip().lower()) or f"No forecast available for {city!r}."


def text_result(text: str) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": text}]}


def error_result(text: str) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": text}], "is_error": True}


@tool(
    "search_flights",
    "Search flights from an origin city or airport to a destination city.",
    {"origin": str, "destination": str},
)
async def search_flights(args: dict[str, Any]) -> dict[str, Any]:
    try:
        return text_result(flights_report(args["origin"], args["destination"]))
    except KeyError as e:
        return error_result(f"Error: missing argument {e}")


@tool("search_hotels", "Search hotels in a city.", {"city": str})
async def search_hotels(args: dict[str, Any]) -> dict[str, Any]:
    try:
        return text_result(hotels_report(args["city"]))
    except KeyError as e:
        return error_result(f"Error: missing argument {e}")


@tool("get_forecast", "Get the weekend weather forecast for a city.", {"city": str})
async def get_forecast(args: dict[str, Any]) -> dict[str, Any]:
    try:
        return text_result(forecast_report(args["city"]))
    except KeyError as e:
        return error_result(f"Error: missing argument {e}")
