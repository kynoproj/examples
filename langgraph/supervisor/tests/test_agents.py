from unittest.mock import AsyncMock

from langchain_core.messages import AIMessage

from assistant.agents import build_calculator, build_researcher, build_supervisor
from conftest import ScriptedChatModel, tool_call


async def test_supervisor_delegates_to_both_workers_in_order():
    ask_peer = AsyncMock(side_effect=["France: ~68 million people.", "204"])
    llm = ScriptedChatModel(
        responses=[
            tool_call("ask_researcher", question="population of France"),
            tool_call("ask_calculator", problem="68 * 3"),
            AIMessage(content="France's population times 3 is about 204 million."),
        ]
    )

    result = await build_supervisor(llm, ask_peer).ainvoke(
        {"messages": [{"role": "user", "content": "population of France times 3?"}]}
    )

    assert [c.args for c in ask_peer.await_args_list] == [
        ("researcher", "population of France"),
        ("calculator", "68 * 3"),
    ]
    assert result["messages"][-1].content.endswith("204 million.")


async def test_supervisor_routes_single_worker():
    ask_peer = AsyncMock(return_value="Paris")
    llm = ScriptedChatModel(
        responses=[tool_call("ask_researcher", question="capital of France"), AIMessage(content="Paris.")]
    )

    await build_supervisor(llm, ask_peer).ainvoke(
        {"messages": [{"role": "user", "content": "capital of France?"}]}
    )

    ask_peer.assert_awaited_once_with("researcher", "capital of France")


async def test_researcher_uses_lookup_tool():
    llm = ScriptedChatModel(
        responses=[tool_call("lookup_fact", topic="Japan"), AIMessage(content="Tokyo.")]
    )

    result = await build_researcher(llm).ainvoke({"messages": [{"role": "user", "content": "Japan?"}]})

    assert any("124 million" in str(m.content) for m in result["messages"])


async def test_calculator_uses_arithmetic_tool():
    llm = ScriptedChatModel(
        responses=[tool_call("multiply", a=68, b=3), AIMessage(content="204")]
    )

    result = await build_calculator(llm).ainvoke({"messages": [{"role": "user", "content": "68*3"}]})

    assert result["messages"][-1].content == "204"
    assert any(str(m.content) == "204.0" for m in result["messages"][:-1])
