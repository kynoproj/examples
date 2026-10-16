from unittest.mock import AsyncMock

from fakes import call, scripted, text

from adk_travel.agent import run_agent
from adk_travel.discovery import WorkerInfo
from adk_travel.supervisor import (
    build_instruction,
    build_supervisor_runner,
    peer_tools,
    tool_name,
)

FLIGHTS = WorkerInfo("flights", "Finds flights", (("Search flights", "Times and prices"),))
HOTELS = WorkerInfo("hotels", "Finds hotels", ())
WEATHER = WorkerInfo("weather", "Weekend forecast", ())


def names(runner):
    return [t.__name__ for t in runner.agent.tools]


def test_one_tool_per_worker_described_from_its_card():
    tools = peer_tools((FLIGHTS, HOTELS), AsyncMock())

    assert [t.__name__ for t in tools] == ["ask_flights", "ask_hotels"]
    assert "Finds flights" in tools[0].__doc__
    assert "Search flights: Times and prices" in tools[0].__doc__


def test_tool_name_is_sanitized():
    assert tool_name("my worker.v2-a") == "ask_my_worker_v2_a"


def test_instruction_lists_exactly_the_discovered_workers():
    instruction = build_instruction((FLIGHTS, HOTELS))
    assert "ask_flights" in instruction and "ask_hotels" in instruction
    assert "ask_weather" not in instruction


def test_instruction_with_no_workers_says_so():
    assert "no workers" in build_instruction(())


async def test_tool_delegates_to_its_worker_over_a2a():
    ask_peer = AsyncMock(return_value="Sat: sunny")
    tools = {t.__name__: t for t in peer_tools((FLIGHTS, HOTELS, WEATHER), ask_peer)}

    result = await tools["ask_weather"]("Tokyo weekend")

    ask_peer.assert_awaited_once_with("weather", "Tokyo weekend")
    assert result == {"status": "success", "result": "Sat: sunny"}


def test_adding_a_worker_needs_no_code_change():
    """Same code, a different discovered set: only the new worker's tool appears."""
    before = build_supervisor_runner((FLIGHTS, HOTELS), AsyncMock())
    after = build_supervisor_runner((FLIGHTS, HOTELS, WEATHER), AsyncMock())

    assert names(before) == ["ask_flights", "ask_hotels"]
    assert names(after) == [*names(before), "ask_weather"]
    assert "ask_weather" in after.agent.instruction and "ask_weather" not in before.agent.instruction


async def test_worker_failure_is_reported_to_the_model_not_raised():
    ask_peer = AsyncMock(side_effect=RuntimeError("down"))
    (tool,) = peer_tools((FLIGHTS,), ask_peer)

    result = await tool("x")

    assert result["status"] == "error"
    assert "flights" in result["error"] and "down" in result["error"]


def test_supervisor_with_no_workers_has_no_tools_at_all():
    assert names(build_supervisor_runner((), AsyncMock())) == []


async def test_supervisor_run_delegates_and_answers_from_the_worker_reply():
    ask_peer = AsyncMock(return_value="Hotels in Tokyo: Shinjuku Granbell")
    base = build_supervisor_runner((FLIGHTS, HOTELS), ask_peer)
    runner, llm = scripted(
        base,
        call("ask_hotels", request="Hotels in Tokyo"),
        text("Try the Shinjuku Granbell."),
    )

    reply = await run_agent("Where should I stay in Tokyo?", runner=runner)

    assert reply == "Try the Shinjuku Granbell."
    ask_peer.assert_awaited_once_with("hotels", "Hotels in Tokyo")
    declared = [d.name for t in llm.requests[0].config.tools for d in t.function_declarations]
    assert declared == ["ask_flights", "ask_hotels"]
