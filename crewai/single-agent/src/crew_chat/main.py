"""Serve the CrewAI chat agent over A2A via the Kynomesh SDK."""

from __future__ import annotations

import asyncio
import logging
import os
import signal

from a2a.types.a2a_pb2 import AgentCapabilities, AgentCard, AgentInterface, AgentSkill
from a2a.utils.constants import PROTOCOL_VERSION_CURRENT, TransportProtocol
from kynomesh import server

from crew_chat.agent import build_agent, run_agent
from crew_chat.executor import CrewExecutor

logging.basicConfig(level=logging.INFO)


def agent_card() -> AgentCard:
    # URLs are placeholders for local dev; Kynomesh rewrites them in-cluster.
    return AgentCard(
        name="CrewAI Chat Agent",
        description="A conversational CrewAI agent served through Kynomesh",
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
    agent = build_agent()

    async def run(prompt: str) -> str:
        return await run_agent(prompt, agent=agent)

    loop = asyncio.get_running_loop()
    serve_task = asyncio.ensure_future(server.start(CrewExecutor(run), agent_card()))
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, serve_task.cancel)
    try:
        await serve_task
    except asyncio.CancelledError:
        pass


def main() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY must be set (see README)")
    asyncio.run(serve())


if __name__ == "__main__":
    main()
