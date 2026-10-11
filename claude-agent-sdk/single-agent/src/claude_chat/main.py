"""Serve the Claude chat agent over A2A via the Kynomesh SDK."""

from __future__ import annotations

import asyncio
import logging
import os
import signal

from a2a.types.a2a_pb2 import AgentCapabilities, AgentCard, AgentInterface, AgentSkill
from a2a.utils.constants import PROTOCOL_VERSION_CURRENT, TransportProtocol
from kynomesh import server

from claude_chat.agent import run_agent
from claude_chat.executor import ClaudeExecutor

logging.basicConfig(level=logging.INFO)


def agent_card() -> AgentCard:
    # URLs are placeholders for local dev; Kynomesh rewrites them in-cluster.
    return AgentCard(
        name="Claude Chat Agent",
        description="A conversational Claude Agent SDK agent served through Kynomesh",
        version="0.1.0",
        supported_interfaces=[
            AgentInterface(
                url="http://127.0.0.1:8088/a2a/jsonrpc",
                protocol_binding=TransportProtocol.JSONRPC.value,
                protocol_version=PROTOCOL_VERSION_CURRENT,
            ),
            AgentInterface(
                url="127.0.0.1:8089",
                protocol_binding=TransportProtocol.GRPC.value,
                protocol_version=PROTOCOL_VERSION_CURRENT,
            ),
        ],
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[
            AgentSkill(
                id="chat",
                name="Chat",
                description="Brief, friendly replies; converts temperatures with a custom tool",
                tags=["chat"],
                examples=["What is 72 F in Celsius?"],
            )
        ],
    )


async def serve() -> None:
    loop = asyncio.get_running_loop()
    serve_task = asyncio.ensure_future(server.start(ClaudeExecutor(run_agent), agent_card()))
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, serve_task.cancel)
    try:
        await serve_task
    except asyncio.CancelledError:
        pass


def main() -> None:
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise SystemExit("ANTHROPIC_API_KEY must be set (see README)")
    asyncio.run(serve())


if __name__ == "__main__":
    main()
