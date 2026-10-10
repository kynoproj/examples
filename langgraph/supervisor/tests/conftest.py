from __future__ import annotations

from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage


class ScriptedChatModel(FakeMessagesListChatModel):
    """Replays scripted AI messages and tolerates bind_tools()."""

    def bind_tools(self, tools, **kwargs):
        return self


def tool_call(name: str, **args) -> AIMessage:
    return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": f"call-{name}"}])
