import sys

import pytest
from langchain_core.messages import AIMessage

from assistant import main
from conftest import ScriptedChatModel


@pytest.mark.parametrize("role", main.ROLES)
async def test_each_role_builds_a_graph(monkeypatch, role):
    llm = ScriptedChatModel(responses=[AIMessage(content="ok")])
    monkeypatch.setattr(main.agents, "build_llm", lambda: llm)

    graph = main.build_graph(role)

    result = await graph.ainvoke({"messages": [{"role": "user", "content": "hi"}]})
    assert result["messages"][-1].content == "ok"


def test_unknown_role_is_rejected(monkeypatch):
    monkeypatch.setattr(main.agents, "build_llm", lambda: ScriptedChatModel(responses=[]))
    with pytest.raises(ValueError, match="unknown role"):
        main.build_graph("planner")


def test_missing_api_key_exits_with_message(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(sys, "argv", ["x", "--role", "calculator"])

    with pytest.raises(SystemExit, match="OPENAI_API_KEY"):
        main.main()


def test_main_serves_the_requested_role(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    monkeypatch.setattr(sys, "argv", ["x", "--role", "calculator"])
    served = []

    async def fake_serve(role):
        served.append(role)

    monkeypatch.setattr(main, "serve", fake_serve)
    main.main()

    assert served == ["calculator"]
