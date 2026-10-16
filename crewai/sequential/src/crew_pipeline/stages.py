"""The stages this image can run. Which ones exist, and in what order, is decided by
the AgentSet manifest: a stage never names the one after it."""

from __future__ import annotations

from dataclasses import dataclass

from crewai.tools import BaseTool

from crew_pipeline.tools import lookup_fact, word_count


@dataclass(frozen=True)
class StageSpec:
    name: str  # shown on the card
    description: str
    instruction: str
    tools: tuple[BaseTool, ...]
    output_label: str  # what this stage hands to the next one
    example: str


STAGES: dict[str, StageSpec] = {
    "researcher": StageSpec(
        name="Researcher",
        description="Gathers the key facts about a topic",
        instruction=(
            "You research the topic in the request. Use lookup_fact, then reply with a short "
            "bulleted list of the key facts. Do not write the article."
        ),
        tools=(lookup_fact,),
        output_label="Research notes",
        example="Write a short blurb about Kubernetes",
    ),
    "writer": StageSpec(
        name="Writer",
        description="Writes a short draft from research notes",
        instruction=(
            "The message holds a request followed by research notes. Turn the notes into a short, "
            "engaging draft of two or three sentences that answers the request. Reply with the "
            "draft only."
        ),
        tools=(),
        output_label="Draft",
        example="Research notes: Kubernetes schedules containers onto a cluster",
    ),
    "editor": StageSpec(
        name="Editor",
        description="Edits a draft for clarity and length",
        instruction=(
            "The message holds a request, research notes and a draft. Edit the draft for clarity and "
            "keep it under 60 words. Use word_count to check the length of your final text. "
            "Reply with the final text only."
        ),
        tools=(word_count,),
        output_label="Final text",
        example="Draft: Kubernetes is a system that runs containers on many machines",
    ),
}
ROLES = tuple(STAGES)
