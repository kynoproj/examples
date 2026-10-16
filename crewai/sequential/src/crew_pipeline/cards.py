"""AgentCards, one per stage."""

from __future__ import annotations

from a2a.types.a2a_pb2 import AgentCapabilities, AgentCard, AgentInterface, AgentSkill
from a2a.utils.constants import PROTOCOL_VERSION_CURRENT, TransportProtocol

from crew_pipeline.stages import ROLES, STAGES


def agent_card(role: str) -> AgentCard:
    if role not in STAGES:
        raise ValueError(f"unknown role {role!r}; expected one of {ROLES}")
    spec = STAGES[role]
    # URLs are placeholders for local dev; Kynomesh rewrites them in-cluster.
    return AgentCard(
        name=spec.name,
        description=spec.description,
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
                id=role,
                name=spec.name,
                description=spec.description,
                tags=[role],
                examples=[spec.example],
            )
        ],
    )
