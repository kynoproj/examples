from unittest.mock import AsyncMock

from claude_travel.discovery import WorkerInfo
from claude_travel.supervisor import (
    build_prompt,
    peer_tools,
    supervisor_options,
    tool_name,
)

FLIGHTS = WorkerInfo("flights", "Finds flights", (("Search flights", "Times and prices"),))
HOTELS = WorkerInfo("hotels", "Finds hotels", ())
WEATHER = WorkerInfo("weather", "Weekend forecast", ())


def test_one_tool_per_worker_described_from_its_card():
    tools = peer_tools((FLIGHTS, HOTELS), AsyncMock())

    assert [t.name for t in tools] == ["ask_flights", "ask_hotels"]
    assert "Finds flights" in tools[0].description
    assert "Search flights: Times and prices" in tools[0].description


def test_tool_name_is_sanitized():
    assert tool_name("my worker.v2") == "ask_my_worker_v2"


def test_prompt_lists_exactly_the_discovered_workers():
    prompt = build_prompt((FLIGHTS, HOTELS))
    assert "ask_flights" in prompt and "ask_hotels" in prompt
    assert "ask_weather" not in prompt


def test_prompt_with_no_workers_says_so():
    assert "no workers" in build_prompt(())


async def test_tool_delegates_to_its_worker_over_a2a():
    ask_peer = AsyncMock(return_value="Sat: sunny")
    tools = {t.name: t for t in peer_tools((FLIGHTS, HOTELS, WEATHER), ask_peer)}

    result = await tools["ask_weather"].handler({"request": "Tokyo weekend"})

    ask_peer.assert_awaited_once_with("weather", "Tokyo weekend")
    assert result == {"content": [{"type": "text", "text": "Sat: sunny"}]}


async def test_adding_a_worker_needs_no_code_change():
    """Same code, a different discovered set: only the new worker's tool appears."""
    before = supervisor_options((FLIGHTS, HOTELS), AsyncMock())
    after = supervisor_options((FLIGHTS, HOTELS, WEATHER), AsyncMock())

    assert before.allowed_tools == ["mcp__tools__ask_flights", "mcp__tools__ask_hotels"]
    assert after.allowed_tools == [*before.allowed_tools, "mcp__tools__ask_weather"]
    assert "ask_weather" in after.system_prompt and "ask_weather" not in before.system_prompt


async def test_worker_failure_is_reported_to_the_model_not_raised():
    ask_peer = AsyncMock(side_effect=RuntimeError("down"))
    (tool,) = peer_tools((FLIGHTS,), ask_peer)

    result = await tool.handler({"request": "x"})

    assert result["is_error"] is True
    assert "flights" in result["content"][0]["text"] and "down" in result["content"][0]["text"]


async def test_missing_request_argument_is_reported_to_the_model():
    (tool,) = peer_tools((FLIGHTS,), AsyncMock())

    result = await tool.handler({})

    assert result["is_error"] is True


def test_supervisor_is_locked_down_and_can_only_call_workers():
    options = supervisor_options((FLIGHTS,), AsyncMock())

    assert options.tools == []
    assert options.permission_mode == "dontAsk"
    assert options.allowed_tools == ["mcp__tools__ask_flights"]


def test_supervisor_with_no_workers_has_no_tools_at_all():
    options = supervisor_options((), AsyncMock())

    assert options.allowed_tools == [] and options.mcp_servers == {}
