"""A scripted CrewAI model: replays ReAct-formatted replies, one per model call."""

from crewai.llms.base_llm import BaseLLM


class ScriptedLlm(BaseLLM):
    script: list[str] = []
    seen: list = []

    def call(self, messages, tools=None, callbacks=None, available_functions=None, **kwargs):
        self.seen.append(messages)
        return self.script[len(self.seen) - 1]

    def supports_function_calling(self) -> bool:
        return False  # CrewAI falls back to its ReAct text format


def scripted(*script: str) -> ScriptedLlm:
    return ScriptedLlm(model="scripted", script=list(script), seen=[])


def use_tool(name: str, **args) -> str:
    import json

    return f"Thought: I should use a tool.\nAction: {name}\nAction Input: {json.dumps(args)}"


def final(answer: str) -> str:
    return f"Thought: I now know the final answer\nFinal Answer: {answer}"


class NativeScriptedLlm(ScriptedLlm):
    """Like ScriptedLlm, but takes the native function-calling path (OpenAI's default)."""

    script: list = []

    def supports_function_calling(self) -> bool:
        return True


def native_tool_call(name: str, **args) -> list[dict]:
    import json

    return [{"id": f"call-{name}", "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}]


def native(*script) -> NativeScriptedLlm:
    return NativeScriptedLlm(model="scripted", script=list(script), seen=[])
