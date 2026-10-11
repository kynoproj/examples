"""Worker tools: deterministic stubs over small built-in data. No Kynomesh imports."""

from __future__ import annotations

from langchain_core.tools import tool

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


def _lookup(table: dict, city: str):
    return table.get(city.strip().lower())


@tool
def search_flights(origin: str, destination: str) -> str:
    """Search flights from an origin city or airport to a destination city."""
    options = _lookup(_FLIGHTS, destination)
    if not options:
        return f"No flights found to {destination!r}."
    return f"Flights {origin} -> {destination}:\n" + "\n".join(options)


@tool
def search_hotels(city: str) -> str:
    """Search hotels in a city."""
    options = _lookup(_HOTELS, city)
    if not options:
        return f"No hotels found in {city!r}."
    return f"Hotels in {city}:\n" + "\n".join(options)


@tool
def get_forecast(city: str) -> str:
    """Get the weekend weather forecast for a city."""
    return _lookup(_FORECASTS, city) or f"No forecast available for {city!r}."
