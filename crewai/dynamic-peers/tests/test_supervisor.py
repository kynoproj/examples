import asyncio

import pytest
from fakes import final, native, native_tool_call, scripted, use_tool

from crew_travel.agent import run_agent
from crew_travel.discovery import WorkerInfo
from crew_travel.peers import blocking_ask
from crew_travel.supervisor import (
    build_instruction,
    build_supervisor,
    peer_tools,
    tool_name,
)

FLIGHTS = WorkerInfo("flights", "Finds flights", (("Search flights", "Times and prices"),))
HOTELS = WorkerInfo("hotels", "Finds hotels", ())
WEATHER = WorkerInfo("weather", "Weekend forecast", ())


def never(name, text):
    raise AssertionError("no peer should be called")


def names(agent):
    return [t.name for t in agent.tools]


def test_one_tool_per_worker_described_from_its_card():
    tools = peer_tools((FLIGHTS, HOTELS), never)

    assert [t.name for t in tools] == ["ask_flights", "ask_hotels"]
    assert "Finds flights" in tools[0].description
    assert "Search flights: Times and prices" in tools[0].description


def test_tool_name_is_sanitized():
    assert tool_name("my worker.v2-a") == "ask_my_worker_v2_a"


def test_instruction_lists_exactly_the_discovered_workers():
    instruction = build_instruction((FLIGHTS, HOTELS))
    assert "ask_flights" in instruction and "ask_hotels" in instruction
    assert "ask_weather" not in instruction


def test_instruction_with_no_workers_says_so():
    assert "no workers" in build_instruction(())


def test_tool_delegates_to_its_worker_over_a2a():
    asked = []
    tools = {t.name: t for t in peer_tools((FLIGHTS, HOTELS, WEATHER), lambda n, t: asked.append((n, t)) or "Sat: sunny")}

    result = tools["ask_weather"].run(request="Tokyo weekend")

    assert asked == [("weather", "Tokyo weekend")]
    assert result == "Sat: sunny"


def test_adding_a_worker_needs_no_code_change():
    """Same code, a different discovered set: only the new worker's tool appears."""
    before = build_supervisor((FLIGHTS, HOTELS), never, scripted())
    after = build_supervisor((FLIGHTS, HOTELS, WEATHER), never, scripted())

    assert names(before) == ["ask_flights", "ask_hotels"]
    assert names(after) == [*names(before), "ask_weather"]
    assert "ask_weather" in after.backstory and "ask_weather" not in before.backstory


def test_worker_failure_is_reported_to_the_model_not_raised():
    def ask_peer(name, text):
        raise RuntimeError("down")

    (tool,) = peer_tools((FLIGHTS,), ask_peer)

    result = tool.run(request="x")

    assert "flights" in result and "down" in result and result.startswith("Error")


def test_supervisor_with_no_workers_has_no_tools_at_all():
    assert names(build_supervisor((), never, scripted())) == []


@pytest.mark.parametrize("function_calling", [False, True], ids=["react", "native-function-calling"])
async def test_supervisor_run_delegates_over_the_servers_loop_and_answers(function_calling):
    server_loop = asyncio.get_running_loop()
    seen = {}

    async def ask_peer(name, text):
        seen["call"] = (name, text, asyncio.get_running_loop())
        return "Hotels in Tokyo: Shinjuku Granbell"

    if function_calling:
        llm = native(native_tool_call("ask_hotels", request="Hotels in Tokyo"), "Try the Shinjuku Granbell.")
    else:
        llm = scripted(use_tool("ask_hotels", request="Hotels in Tokyo"), final("Try the Shinjuku Granbell."))
    agent = build_supervisor((FLIGHTS, HOTELS), blocking_ask(ask_peer, server_loop), llm)

    reply = await run_agent("Where should I stay in Tokyo?", agent=agent)

    assert reply == "Try the Shinjuku Granbell."
    assert seen["call"] == ("hotels", "Hotels in Tokyo", server_loop)
