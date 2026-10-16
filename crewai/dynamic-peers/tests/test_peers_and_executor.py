from types import SimpleNamespace
from unittest.mock import patch

import pytest
from a2a.types.a2a_pb2 import Message, Part, Role, StreamResponse

from crew_travel import peers
from crew_travel.executor import CrewExecutor, message_text


class _FakeA2AClient:
    def __init__(self, texts):
        self._texts = texts
        self.requests = []

    async def send_message(self, request):
        self.requests.append(request)
        for text in self._texts:
            yield StreamResponse(message=Message(message_id="m", role=Role.ROLE_AGENT, parts=[Part(text=text)]))


async def test_ask_peer_joins_reply_text():
    fake = _FakeA2AClient(["204", " million"])

    async def fake_peer_client(name):
        assert name == "calculator"
        return fake

    with patch.object(peers.client, "peer_client", fake_peer_client):
        reply = await peers.ask_peer("calculator", "68 * 3")

    assert reply == "204 million"
    assert message_text(fake.requests[0].message) == "68 * 3"


async def test_ask_peer_empty_reply_raises():
    async def fake_peer_client(name):
        return _FakeA2AClient([])

    with patch.object(peers.client, "peer_client", fake_peer_client):
        with pytest.raises(peers.PeerReplyError):
            await peers.ask_peer("calculator", "hi")


async def test_executor_runs_agent_and_replies_with_its_text():
    seen = []

    async def run(prompt: str) -> str:
        seen.append(prompt)
        return "pong"

    events = []

    class Queue:
        async def enqueue_event(self, event):
            events.append(event)

    ctx = SimpleNamespace(message=Message(message_id="1", role=Role.ROLE_USER, parts=[Part(text="ping")]))
    await CrewExecutor(run).execute(ctx, Queue())

    assert seen == ["ping"]
    assert message_text(events[0]) == "pong"
    assert events[0].role == Role.ROLE_AGENT


def test_message_text_handles_missing_message():
    assert message_text(None) == ""
