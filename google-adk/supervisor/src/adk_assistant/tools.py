"""Worker tools. Plain functions with no Kynomesh imports.

ADK builds each tool's schema from the signature and docstring. Each returns a
dict, with `status` telling the model whether the call worked.
"""

from __future__ import annotations

KNOWLEDGE_BASE: dict[str, str] = {
    "france": "France is a country in Western Europe. Capital: Paris. Population: about 68 million.",
    "japan": "Japan is an island country in East Asia. Capital: Tokyo. Population: about 124 million.",
    "kubernetes": "Kubernetes is an open-source container orchestration system originally built at Google.",
    "a2a": "A2A (Agent2Agent) is an open protocol that lets AI agents discover and call each other.",
}


def ok(result: str | float) -> dict:
    return {"status": "success", "result": result}


def failed(error: str) -> dict:
    return {"status": "error", "error": error}


def lookup_fact(topic: str) -> dict:
    """Look up a short fact about a topic (e.g. a country or technology).

    Args:
        topic: The topic to look up.
    """
    needle = topic.strip().lower()
    for key, fact in KNOWLEDGE_BASE.items():
        if key in needle or needle in key:
            return ok(fact)
    return ok(f"No facts found for {topic!r}.")


def add(a: float, b: float) -> dict:
    """Add two numbers.

    Args:
        a: The first number.
        b: The second number.
    """
    return ok(a + b)


def multiply(a: float, b: float) -> dict:
    """Multiply two numbers.

    Args:
        a: The first number.
        b: The second number.
    """
    return ok(a * b)


def divide(a: float, b: float) -> dict:
    """Divide a by b.

    Args:
        a: The dividend.
        b: The divisor.
    """
    if b == 0:
        return failed("division by zero")
    return ok(a / b)


RESEARCHER_TOOLS = [lookup_fact]
CALCULATOR_TOOLS = [add, multiply, divide]
