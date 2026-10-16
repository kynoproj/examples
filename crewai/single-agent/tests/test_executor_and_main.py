import sys
from types import SimpleNamespace

import pytest
from a2a.types.a2a_pb2 import Message, Part, Role

from crew_chat import main
from crew_chat.executor import CrewExecutor, message_text


class Queue:
    def __init__(self):
        self.events = []

    async def enqueue_event(self, event):
        self.events.append(event)


def ctx(text: str):
    return SimpleNamespace(message=Message(message_id="1", role=Role.ROLE_USER, parts=[Part(text=text)]))


async def test_executor_runs_agent_and_replies_with_its_text():
    seen = []

    async def run(prompt: str) -> str:
        seen.append(prompt)
        return "pong"

    queue = Queue()
    await CrewExecutor(run).execute(ctx("ping"), queue)

    assert seen == ["ping"]
    assert message_text(queue.events[0]) == "pong"
    assert queue.events[0].role == Role.ROLE_AGENT


async def test_executor_propagates_agent_errors():
    async def run(prompt: str) -> str:
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        await CrewExecutor(run).execute(ctx("x"), Queue())


def test_message_text_handles_missing_message():
    assert message_text(None) == ""


def test_card_advertises_protocol_version_on_every_interface():
    card = main.agent_card()
    assert card.skills
    assert all(i.protocol_version for i in card.supported_interfaces)


def test_missing_api_key_exits_with_message(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(SystemExit, match="OPENAI_API_KEY"):
        main.main()


def test_main_serves_when_key_is_set(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    served = []

    async def fake_serve():
        served.append(True)

    monkeypatch.setattr(main, "serve", fake_serve)
    main.main()

    assert served == [True]
