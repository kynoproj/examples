import pytest
from fakes import final, scripted, use_tool

from crew_travel.agent import DEFAULT_MODEL, AgentError, build_agent, run_agent
from crew_travel.tools import get_forecast


def weather(llm=None):
    return build_agent(role="weather", instruction="Be brief.", tools=[get_forecast], llm=llm)


def test_agent_has_exactly_the_given_tools():
    assert [t.name for t in weather(scripted()).tools] == ["get_forecast"]


def test_model_comes_from_env(monkeypatch):
    monkeypatch.setenv("OPENAI_MODEL", "gpt-custom")
    assert weather().llm.model == "gpt-custom"


def test_model_defaults(monkeypatch):
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    assert weather().llm.model == DEFAULT_MODEL


async def test_calls_the_tool_and_replies():
    llm = scripted(use_tool("get_forecast", city="Tokyo"), final("Sunny then rain."))

    assert await run_agent("Weather in Tokyo?", agent=weather(llm)) == "Sunny then rain."
    assert "light rain" in str(llm.seen[1])


async def test_empty_answer_raises():
    with pytest.raises(AgentError, match="without a final answer"):
        await run_agent("hi", agent=weather(scripted(final(""))))
