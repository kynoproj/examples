from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from chat_agent.graph import graph

PATCH = "chat_agent.graph.AsyncOpenAI"


def _client(create: AsyncMock) -> SimpleNamespace:
    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))


def _completion(text: str) -> SimpleNamespace:
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=text))])


async def test_appends_assistant_reply():
    create = AsyncMock(return_value=_completion("Hi there!"))
    with patch(PATCH, return_value=_client(create)):
        result = await graph.ainvoke({"messages": [{"role": "user", "content": "hello"}]})

    assert result["messages"][-1] == {"role": "assistant", "content": "Hi there!"}
    assert result["messages"][0]["content"] == "hello"
    sent = create.await_args.kwargs["messages"]
    assert sent[-1] == {"role": "user", "content": "hello"}


async def test_openai_failure_is_reported_in_reply():
    create = AsyncMock(side_effect=RuntimeError("boom"))
    with patch(PATCH, return_value=_client(create)):
        result = await graph.ainvoke({"messages": [{"role": "user", "content": "hello"}]})

    assert "trouble processing" in result["messages"][-1]["content"]
