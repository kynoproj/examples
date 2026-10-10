"""Calling a peer agent over A2A through the Kynomesh SDK."""

from __future__ import annotations

import uuid

from a2a.types.a2a_pb2 import Message, Part, Role, SendMessageRequest
from kynomesh import client


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
