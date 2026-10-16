"""Calling a peer agent over A2A through the Kynomesh SDK."""

from __future__ import annotations

import asyncio
import uuid
from typing import Awaitable, Callable

from a2a.types.a2a_pb2 import Message, Part, Role, SendMessageRequest
from kynomesh import client

PEER_TIMEOUT = 120.0  # seconds a tool waits for a worker's reply


class PeerReplyError(RuntimeError):
    """The peer answered without any text."""


async def ask_peer(name: str, text: str) -> str:
    """Send `text` to the peer `name` and return the text of its reply.

    `peer_client` resolves the peer from the AgentSet topology and caches the
    A2A client, so no URLs appear here.
    """
    a2a_client = await client.peer_client(name)
    request = SendMessageRequest(
        message=Message(
            message_id=str(uuid.uuid4()),
            role=Role.ROLE_USER,
            parts=[Part(text=text)],
        )
    )
    chunks: list[str] = []
    async for response in a2a_client.send_message(request):
        chunks.extend(part.text for part in response.message.parts)
    reply = "".join(chunks)
    if not reply:
        raise PeerReplyError(f"peer {name!r} returned no text")
    return reply


def blocking_ask(
    ask: Callable[[str, str], Awaitable[str]],
    loop: asyncio.AbstractEventLoop,
    *,
    timeout: float = PEER_TIMEOUT,
) -> Callable[[str, str], str]:
    """A synchronous `ask(name, text)` that runs `ask` on `loop` and waits for it.

    CrewAI runs a tool on a worker thread with its own event loop, but the
    Kynomesh client caches peer connections for a single event loop. So the call
    is handed back to the server's loop instead of being awaited where the tool
    happens to run.
    """

    def call(name: str, text: str) -> str:
        try:
            on_loop_thread = asyncio.get_running_loop() is loop
        except RuntimeError:
            on_loop_thread = False
        if on_loop_thread:  # waiting here would block the loop that must run the call
            raise RuntimeError("blocking_ask called on the event loop thread; it would deadlock")
        future = asyncio.run_coroutine_threadsafe(ask(name, text), loop)
        try:
            return future.result(timeout)
        except TimeoutError:
            future.cancel()
            raise TimeoutError(f"peer {name!r} did not reply within {timeout:g}s") from None

    return call
