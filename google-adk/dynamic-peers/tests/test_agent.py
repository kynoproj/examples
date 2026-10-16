import pytest
from fakes import call, scripted, text
from google.adk.models import LlmResponse
from google.genai import types

from adk_travel.agent import DEFAULT_MODEL, AgentError, build_runner, run_agent
from adk_travel.tools import get_forecast


def runner(*script):
    base = build_runner(name="weather", instruction="Be brief.", tools=[get_forecast])
    return scripted(base, *script)


def test_agent_has_exactly_the_given_tools():
    agent = build_runner(name="weather", instruction="x", tools=[get_forecast]).agent
    assert [t.__name__ for t in agent.tools] == ["get_forecast"]


def test_model_comes_from_env(monkeypatch):
    monkeypatch.setenv("GOOGLE_MODEL", "gemini-custom")
    assert build_runner(name="a", instruction="x", tools=[]).agent.model == "gemini-custom"


def test_model_defaults(monkeypatch):
    monkeypatch.delenv("GOOGLE_MODEL", raising=False)
    assert build_runner(name="a", instruction="x", tools=[]).agent.model == DEFAULT_MODEL


async def test_calls_the_tool_and_replies():
    r, llm = runner(call("get_forecast", city="Tokyo"), text("Sunny then rain."))

    assert await run_agent("Weather in Tokyo?", runner=r) == "Sunny then rain."
    response = llm.requests[1].contents[-1].parts[0].function_response
    assert "rain" in response.response["result"]


async def test_error_event_raises():
    r, _ = runner(LlmResponse(error_code="SAFETY", error_message="blocked"))

    with pytest.raises(AgentError, match="SAFETY"):
        await run_agent("hi", runner=r)


async def test_empty_reply_raises():
    r, _ = runner(LlmResponse(content=types.Content(role="model", parts=[])))

    with pytest.raises(AgentError, match="without a final response"):
        await run_agent("hi", runner=r)
