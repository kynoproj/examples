from types import SimpleNamespace
from unittest.mock import patch

import pytest
from a2a.types.a2a_pb2 import Message, Part, Role, StreamResponse

from travel import peers
from travel.executor import LangGraphExecutor, message_text


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


async def test_executor_maps_messages_in_and_out():
    seen = {}

    class FakeGraph:
        async def ainvoke(self, state):
            seen.update(state)
            return {"messages": [SimpleNamespace(content="pong")]}

    events = []

    class Queue:
        async def enqueue_event(self, event):
            events.append(event)

    ctx = SimpleNamespace(message=Message(message_id="1", role=Role.ROLE_USER, parts=[Part(text="ping")]))
    await LangGraphExecutor(FakeGraph()).execute(ctx, Queue())

    assert seen == {"messages": [{"role": "user", "content": "ping"}]}
    assert message_text(events[0]) == "pong"
