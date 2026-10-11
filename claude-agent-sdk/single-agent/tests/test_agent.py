import pytest
from claude_agent_sdk import ResultMessage

from claude_chat.agent import AgentError, build_options, run_agent


def result(text: str | None = "hi", *, is_error: bool = False, subtype: str = "success", errors=None):
    return ResultMessage(
        subtype=subtype,
        duration_ms=1,
        duration_api_ms=1,
        is_error=is_error,
        num_turns=1,
        session_id="s",
        result=text,
        errors=errors,
    )


def fake_query(*messages):
    async def query(*, prompt, options):
        query.calls.append((prompt, options))
        for m in messages:
            yield m

    query.calls = []
    return query


def test_options_are_locked_down_for_running_in_a_pod():
    options = build_options()

    assert options.tools == []  # no Bash/Read/Write/...
    assert options.permission_mode == "dontAsk"
    assert options.setting_sources == []
    assert options.strict_mcp_config is True
    assert options.allowed_tools == ["mcp__tools__convert_temperature"]
    assert list(options.mcp_servers) == ["tools"]
    assert options.max_turns


def test_model_comes_from_env(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")
    assert build_options().model == "claude-sonnet-5-5"


def test_model_defaults_to_sdk_choice(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)
    assert build_options().model is None


async def test_returns_final_result_text():
    query = fake_query(object(), result("Hello!"))

    assert await run_agent("hi", query_fn=query) == "Hello!"
    assert query.calls[0][0] == "hi"


async def test_none_result_becomes_empty_string():
    assert await run_agent("hi", query_fn=fake_query(result(None))) == ""


async def test_error_result_raises():
    query = fake_query(result(None, is_error=True, subtype="error_max_turns", errors=["too many turns"]))

    with pytest.raises(AgentError, match="error_max_turns"):
        await run_agent("hi", query_fn=query)


async def test_missing_result_raises():
    with pytest.raises(AgentError, match="without a result"):
        await run_agent("hi", query_fn=fake_query(object()))
