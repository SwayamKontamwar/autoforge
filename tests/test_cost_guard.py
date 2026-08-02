"""This experiment must cost nothing, forever, with nobody watching it.

Every way it could start costing money is silent: a repository flipped to
private still builds, a bigger runner label is one word, and repointing
``LLM_BASE_URL`` at a paid API still succeeds -- the bill just turns up later.
These tests pin the refusals, and pin the workflow wiring that feeds them, so
the guard cannot be unplugged without the guardrail catching it.
"""

import re
from pathlib import Path

import pytest

from builder import cost, run

WORKFLOW = Path(__file__).resolve().parent.parent / ".github" / "workflows" / "daily-build.yml"


@pytest.mark.parametrize("visibility", ["private", "internal", "Private", " PRIVATE "])
def test_refuses_metered_repository_visibility(visibility):
    with pytest.raises(cost.WouldCostMoney, match="meters Actions minutes"):
        cost.check_visibility(visibility)


@pytest.mark.parametrize("visibility", ["public", None, ""])
def test_allows_free_repository_visibility(visibility):
    cost.check_visibility(visibility)


@pytest.mark.parametrize(
    "runner",
    ["ubuntu-latest-4-cores", "ubuntu-latest-16-core", "ubuntu-latest-xlarge", "gpu-runner"],
)
def test_refuses_paid_runners(runner):
    with pytest.raises(cost.WouldCostMoney, match="paid runner"):
        cost.check_runner(runner)


@pytest.mark.parametrize("runner", ["ubuntu-latest", "ubuntu-24.04", "self-hosted", None, ""])
def test_allows_free_runners(runner):
    cost.check_runner(runner)


@pytest.mark.parametrize(
    "url",
    [
        "https://api.openai.com/v1",
        "https://api.anthropic.com/v1",
        "https://my-thing.openai.azure.com/v1",
        "https://api.mistral.ai/v1",
        "https://api.deepseek.com/v1",
        "https://api.together.xyz/v1",
    ],
)
def test_refuses_endpoints_that_are_not_known_to_be_free(url):
    with pytest.raises(cost.WouldCostMoney, match="not on the list of endpoints known to be free"):
        cost.check_endpoint("openai", url)


@pytest.mark.parametrize(
    "url",
    [
        "https://api.groq.com/openai/v1",
        "http://localhost:11434/v1",
        "http://127.0.0.1:8080/v1",
        "http://my-box.local/v1",
    ],
)
def test_allows_endpoints_known_to_be_free(url):
    cost.check_endpoint("openai", url)


def test_refuses_a_paid_provider_with_no_endpoint_at_all():
    with pytest.raises(cost.WouldCostMoney, match="no LLM_BASE_URL"):
        cost.check_endpoint("openai", None)


@pytest.mark.parametrize("provider", ["mock", "github"])
def test_free_providers_need_no_endpoint(provider):
    cost.check_endpoint(provider, None)


def test_preflight_refuses_before_anything_is_spent():
    env = {
        "FORGE_REPO_VISIBILITY": "private",
        "FORGE_RUNNER": "ubuntu-latest",
        "LLM_BASE_URL": "https://api.groq.com/openai/v1",
    }
    with pytest.raises(cost.WouldCostMoney):
        cost.preflight("openai", env)


def test_preflight_passes_the_real_configuration():
    env = {
        "FORGE_REPO_VISIBILITY": "public",
        "FORGE_RUNNER": "ubuntu-latest",
        "LLM_BASE_URL": "https://api.groq.com/openai/v1",
    }
    cost.preflight("openai", env)


def test_run_refuses_and_never_touches_the_repository(tmp_path, monkeypatch, capsys):
    """The refusal must come first -- before the model, the guardrail, or git."""
    monkeypatch.setenv("FORGE_REPO_VISIBILITY", "private")
    called = []
    monkeypatch.setattr(run, "get_provider", lambda name: called.append(name))
    monkeypatch.setattr(run, "_is_clean", lambda root: called.append("is_clean") or True)

    exit_code = run.main(["--provider", "mock", "--repo-root", str(tmp_path), "--no-push"])

    assert exit_code == 1
    assert called == []
    assert "refusing to run" in capsys.readouterr().err
    assert not list(tmp_path.iterdir())


# --- the wiring itself, so the guard cannot be quietly unplugged -------------


def _workflow_text():
    return WORKFLOW.read_text(encoding="utf-8")


def test_workflow_tells_the_guard_the_repository_visibility():
    assert "FORGE_REPO_VISIBILITY: ${{ github.event.repository.visibility }}" in _workflow_text()


def test_workflow_declares_the_runner_it_actually_uses():
    text = _workflow_text()
    runs_on = re.search(r"^\s*runs-on:\s*(\S+)\s*$", text, re.M)
    declared = re.search(r"^\s*FORGE_RUNNER:\s*(\S+)\s*$", text, re.M)
    assert runs_on and declared, "workflow must both pick a runner and declare it to the guard"
    assert runs_on.group(1) == declared.group(1), (
        "runs-on and FORGE_RUNNER disagree: the cost guard would be checking a "
        "runner the job does not actually use"
    )
    cost.check_runner(runs_on.group(1))


def test_workflow_has_no_trigger_that_could_loop():
    """A push trigger would make every bot commit start another billable run."""
    text = _workflow_text()
    block = re.search(r"^on:\n(.*?)(?=^\S)", text, re.M | re.S)
    assert block, "workflow must declare its triggers"
    triggers = re.findall(r"^  (\w+):", block.group(1), re.M)
    assert triggers, "no triggers parsed -- the test is not actually checking anything"
    assert set(triggers) <= {"schedule", "workflow_dispatch"}, triggers


def test_workflow_uploads_no_artifacts():
    """Artifact and cache storage is the other thing GitHub bills for."""
    assert "upload-artifact" not in _workflow_text()


# --- the check that sits on the line that actually spends money -------------


def test_paid_endpoint_is_refused_before_the_request_is_made(monkeypatch):
    """The refusal has to come before the HTTP call, not after it."""
    from builder import llm

    monkeypatch.setenv("LLM_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setenv("MODEL_ID", "gpt-4o")
    monkeypatch.setenv("LLM_API_KEY", "sk-would-be-billed")

    def explode(*args, **kwargs):
        raise AssertionError("a request was sent to a paid endpoint")

    monkeypatch.setattr(llm, "_chat_completion", explode)

    provider = llm.get_provider("openai")
    with pytest.raises(cost.WouldCostMoney, match="api.openai.com"):
        provider.generate("do a thing", "some context")


def test_the_real_configuration_still_reaches_the_request(monkeypatch):
    """The guard must not break the free path it exists to protect."""
    from builder import llm

    monkeypatch.setenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
    monkeypatch.setenv("MODEL_ID", "openai/gpt-oss-120b")
    monkeypatch.setenv("LLM_API_KEY", "free-key")

    reached = []
    monkeypatch.setattr(llm, "_chat_completion", lambda *a, **k: reached.append(a) or "")
    monkeypatch.setattr(llm, "parse_patch", lambda raw: "parsed")

    assert llm.get_provider("openai").generate("do a thing", "ctx") == "parsed"
    assert reached, "the free endpoint must still be reached"
