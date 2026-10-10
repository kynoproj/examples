"""Worker tools. Plain LangChain tools with no Kynomesh imports."""

from __future__ import annotations

from langchain_core.tools import tool

KNOWLEDGE_BASE: dict[str, str] = {
    "france": "France is a country in Western Europe. Capital: Paris. Population: about 68 million.",
    "japan": "Japan is an island country in East Asia. Capital: Tokyo. Population: about 124 million.",
    "kubernetes": "Kubernetes is an open-source container orchestration system originally built at Google.",
    "a2a": "A2A (Agent2Agent) is an open protocol that lets AI agents discover and call each other.",
}


@tool
def lookup_fact(topic: str) -> str:
    """Look up a short fact about a topic (e.g. a country or technology)."""
    needle = topic.strip().lower()
    for key, fact in KNOWLEDGE_BASE.items():
        if key in needle or needle in key:
            return fact
    return f"No facts found for {topic!r}."


@tool
def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


@tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b


@tool
def divide(a: float, b: float) -> str:
    """Divide a by b."""
    if b == 0:
        return "Error: division by zero."
    return str(a / b)


RESEARCHER_TOOLS = [lookup_fact]
CALCULATOR_TOOLS = [add, multiply, divide]
