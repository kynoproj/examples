"""The worker roles this image can run. Which ones exist is decided by the AgentSet
manifest, not by the supervisor: it discovers whatever is deployed."""

from __future__ import annotations

from dataclasses import dataclass

from claude_agent_sdk import SdkMcpTool

from claude_travel.tools import get_forecast, search_flights, search_hotels


@dataclass(frozen=True)
class Skill:
    id: str
    name: str
    description: str


@dataclass(frozen=True)
class WorkerSpec:
    description: str
    prompt: str
    tools: tuple[SdkMcpTool, ...]
    skills: tuple[Skill, ...]
    examples: tuple[str, ...]


WORKERS: dict[str, WorkerSpec] = {
    "flights": WorkerSpec(
        description="Finds flights between cities.",
        prompt="You are a flights expert. Use search_flights and report the options briefly.",
        tools=(search_flights,),
        skills=(Skill("search-flights", "Search flights", "Flight options with times and prices"),),
        examples=("Flights from SFO to Tokyo",),
    ),
    "hotels": WorkerSpec(
        description="Finds hotels in a city.",
        prompt="You are a hotels expert. Use search_hotels and report the options briefly.",
        tools=(search_hotels,),
        skills=(Skill("search-hotels", "Search hotels", "Hotel options with nightly prices"),),
        examples=("Hotels in Tokyo",),
    ),
    "weather": WorkerSpec(
        description="Gives the weekend weather forecast for a city.",
        prompt="You are a weather expert. Use get_forecast and report the forecast briefly.",
        tools=(get_forecast,),
        skills=(Skill("weekend-forecast", "Weekend forecast", "Saturday and Sunday forecast"),),
        examples=("Weather in Tokyo this weekend",),
    ),
}
