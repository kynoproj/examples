"""Stage tools. Plain CrewAI tools with no Kynomesh imports."""

from __future__ import annotations

from crewai.tools import tool

KNOWLEDGE_BASE: dict[str, str] = {
    "kubernetes": "Kubernetes is an open-source container orchestration system originally built at Google. "
    "It schedules containers onto a cluster of machines and restarts them when they fail.",
    "a2a": "A2A (Agent2Agent) is an open protocol that lets AI agents discover and call each other. "
    "Each agent publishes an AgentCard describing what it can do.",
    "japan": "Japan is an island country in East Asia. Capital: Tokyo. Population: about 124 million.",
    "france": "France is a country in Western Europe. Capital: Paris. Population: about 68 million.",
}


def count(text: str) -> int:
    return len(text.split())


@tool("lookup_fact")
def lookup_fact(topic: str) -> str:
    """Look up background facts about a topic (e.g. a country or technology)."""
    needle = topic.strip().lower()
    for key, fact in KNOWLEDGE_BASE.items():
        if key in needle or needle in key:
            return fact
    return f"No facts found for {topic!r}."


@tool("word_count")
def word_count(text: str) -> str:
    """Count the words in a text."""
    return f"{count(text)} words"
