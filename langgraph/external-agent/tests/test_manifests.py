"""The two manifests must agree with each other and with the code."""

from pathlib import Path

import pytest
import yaml

from assistant.cards import ROLES

MANIFESTS = Path(__file__).resolve().parent.parent / "manifests"
INSECURE_ENV = "KYNOMESH_INSECURE_TLS_PEERS"


def load(name: str) -> dict:
    return yaml.safe_load((MANIFESTS / name).read_text())


@pytest.fixture(scope="module")
def supervisor_set() -> dict:
    return load("agentset.yaml")


@pytest.fixture(scope="module")
def calculator_set() -> dict:
    return load("calculator-agentset.yaml")


def env_of(agent: dict) -> dict:
    return {e["name"]: e for e in agent["container"].get("env", [])}


def test_calculator_is_not_deployed_in_the_supervisor_set(supervisor_set):
    managed = [a["name"] for a in supervisor_set["spec"]["agents"]]
    external = [a["name"] for a in supervisor_set["spec"]["externalAgents"]]

    assert external == ["calculator"]
    assert "calculator" not in managed


def test_external_agent_is_never_the_entry(supervisor_set):
    spec = supervisor_set["spec"]
    assert spec["entry"] in [a["name"] for a in spec["agents"]]


def test_external_url_points_at_the_calculator_agentset_service(supervisor_set, calculator_set):
    (external,) = supervisor_set["spec"]["externalAgents"]
    agentset = calculator_set["metadata"]["name"]
    (agent,) = calculator_set["spec"]["agents"]

    # An agent in another AgentSet is served at <agentset>-<agent>:8490 over TLS.
    assert external["url"] == f"https://{agentset}-{agent['name']}:8490"


def test_the_external_peer_name_is_the_one_the_supervisor_calls(supervisor_set):
    (external,) = supervisor_set["spec"]["externalAgents"]
    assert external["name"] in ROLES  # ask_calculator -> peer "calculator"


def test_only_the_supervisor_skips_tls_verification_and_only_for_the_calculator(supervisor_set):
    by_name = {a["name"]: env_of(a) for a in supervisor_set["spec"]["agents"]}

    assert by_name["supervisor"][INSECURE_ENV]["value"] == "calculator"
    assert INSECURE_ENV not in by_name["researcher"]


def test_calculator_set_runs_the_calculator_role_as_its_entry(calculator_set):
    spec = calculator_set["spec"]
    (agent,) = spec["agents"]

    assert spec["entry"] == agent["name"] == "calculator"
    assert agent["container"]["args"] == ["--role", "calculator"]


def test_every_agent_reads_the_openai_key_from_the_secret(supervisor_set, calculator_set):
    agents = supervisor_set["spec"]["agents"] + calculator_set["spec"]["agents"]
    for agent in agents:
        ref = env_of(agent)["OPENAI_API_KEY"]["valueFrom"]["secretKeyRef"]
        assert ref == {"name": "openai-api-key", "key": "OPENAI_API_KEY"}
