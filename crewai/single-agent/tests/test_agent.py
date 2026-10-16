import pytest
from fakes import final, scripted, use_tool

from crew_chat.agent import DEFAULT_MODEL, AgentError, build_agent, run_agent


def test_agent_has_only_the_conversion_tool():
    assert [t.name for t in build_agent(scripted()).tools] == ["convert_temperature"]


def test_model_comes_from_env(monkeypatch):
    monkeypatch.setenv("OPENAI_MODEL", "gpt-custom")
    assert build_agent().llm.model == "gpt-custom"


def test_model_defaults(monkeypatch):
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    assert build_agent().llm.model == DEFAULT_MODEL


async def test_returns_the_final_answer():
    agent = build_agent(scripted(final("Hello!")))

    assert await run_agent("hi", agent=agent) == "Hello!"


async def test_calls_the_tool_and_replies_with_its_result():
    llm = scripted(use_tool("convert_temperature", value=72, from_unit="F", to_unit="C"), final("That is 22.22 C."))

    assert await run_agent("What is 72 F in Celsius?", agent=build_agent(llm)) == "That is 22.22 C."
    assert "Observation: 22.22 C" in str(llm.seen[1])  # the second model call saw the tool's output


async def test_each_request_starts_from_a_clean_conversation():
    llm = scripted(final("one"), final("two"))
    agent = build_agent(llm)

    await run_agent("first-request", agent=agent)
    await run_agent("second-request", agent=agent)

    assert "first-request" not in str(llm.seen[1])


async def test_empty_answer_raises():
    with pytest.raises(AgentError, match="without a final answer"):
        await run_agent("hi", agent=build_agent(scripted(final(""))))


async def test_console_panels_are_suppressed(capfd):
    await run_agent("hi", agent=build_agent(scripted(final("quiet"))))

    assert "Completed" not in capfd.readouterr().out
