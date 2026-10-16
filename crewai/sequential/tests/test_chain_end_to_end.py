"""All three real CrewAI stages wired together in-process, with scripted models."""

from fakes import final, scripted, use_tool

from crew_pipeline.agent import build_agent, run_agent
from crew_pipeline.pipeline import chain
from crew_pipeline.stages import STAGES


def build(role, llm, next_peer, ask_peer):
    spec = STAGES[role]
    agent = build_agent(role=spec.name, instruction=spec.instruction, tools=spec.tools, llm=llm)

    async def stage_run(received):
        return await run_agent(received, agent=agent)

    return chain(stage_run=stage_run, label=spec.output_label, next_peer=next_peer, ask_peer=ask_peer)


async def test_request_flows_researcher_to_writer_to_editor_and_the_answer_flows_back():
    llms = {
        "researcher": scripted(use_tool("lookup_fact", topic="Kubernetes"), final("- schedules containers")),
        "writer": scripted(final("Kubernetes runs your containers.")),
        "editor": scripted(use_tool("word_count", text="Kubernetes runs containers."), final("Kubernetes runs containers.")),
    }
    order = {"researcher": "writer", "writer": "editor", "editor": None}
    stages = {}

    async def ask_peer(name, text):
        return await stages[name](text)

    for role in STAGES:
        stages[role] = build(role, llms[role], order[role], ask_peer)

    reply = await stages["researcher"]("Write a short blurb about Kubernetes")

    assert reply == "Kubernetes runs containers."  # the editor's text, returned up the chain
    assert "Observation: Kubernetes is an open-source" in str(llms["researcher"].seen[1])
    # the writer saw the request and the notes; the editor saw the request, notes and draft
    writer_in = "\n".join(m["content"] for m in llms["writer"].seen[0])
    editor_in = "\n".join(m["content"] for m in llms["editor"].seen[0])
    assert "Write a short blurb about Kubernetes" in writer_in and "- schedules containers" in writer_in
    assert "Research notes:\n- schedules containers" in editor_in
    assert "Draft:\nKubernetes runs your containers." in editor_in
    assert "Observation: 3 words" in str(llms["editor"].seen[1])
