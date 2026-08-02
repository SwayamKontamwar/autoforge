"""Refuse to run anywhere that could bill the owner.

This repository is meant to run by itself for years and cost nothing, ever. The
danger is that none of the ways it could start costing money announce themselves.
A repository flipped to private keeps building exactly as before, except the
Actions minutes are now metered. A larger runner label is one word in a YAML
file. Repointing ``LLM_BASE_URL`` at a paid API is one secret edit, and the run
still succeeds -- the bill just arrives at the end of the month.

So this module checks before spending rather than after, and refuses loudly. A
stopped experiment is recoverable; a surprise invoice from a bot nobody was
watching is the thing this project must never do.

The endpoint check is an allow-list on purpose. "Refuse anything I cannot prove
is free" is the only rule that stays correct as new paid APIs appear.
"""

from __future__ import annotations

import os
import re
from urllib.parse import urlparse


class WouldCostMoney(Exception):
    """Raised when continuing could put a charge on somebody's account."""


# GitHub-hosted standard runners are free for public repositories, with no minute
# cap. Self-hosted runners are the owner's own hardware, so they are free too.
_METERED_RUNNER = re.compile(r"(\d+\s*-?\s*core|x?large|gpu|arm64-\d|macos|windows)", re.I)

# Hosts that serve this project's model calls without a payment method on file.
# Groq's free tier hard-fails with HTTP 429 rather than billing; GitHub Models is
# included with a GitHub account; a local endpoint is the owner's own machine.
FREE_ENDPOINTS = frozenset(
    {
        "api.groq.com",
        "models.inference.ai.azure.com",
        "models.github.ai",
        "localhost",
        "127.0.0.1",
        "::1",
        "host.docker.internal",
    }
)

# Providers that never reach a metered endpoint at all.
_FREE_PROVIDERS = frozenset({"mock", "github"})


def check_visibility(visibility: str | None) -> None:
    """Actions minutes are free and uncapped on public repositories only."""
    if visibility is None or not visibility.strip():
        return  # Running outside Actions, or GitHub did not tell us. Nothing is billed.
    value = visibility.strip().lower()
    if value in {"private", "internal"}:
        raise WouldCostMoney(
            f"this repository is {value}, and GitHub meters Actions minutes on "
            f"{value} repositories. On a public repository the same run is free "
            f"and uncapped. Make the repository public again, or delete the "
            f"schedule -- do not let it keep building on metered minutes."
        )


def check_runner(runner: str | None) -> None:
    """Larger GitHub-hosted runners bill per minute even on public repositories."""
    if not runner:
        return
    label = runner.strip()
    if _METERED_RUNNER.search(label):
        raise WouldCostMoney(
            f"runner label {label!r} looks like a paid runner. Larger, GPU, macOS "
            f"and Windows GitHub-hosted runners are billed per minute even on "
            f"public repositories. Use ubuntu-latest, which is free."
        )


def check_endpoint(provider: str, base_url: str | None) -> None:
    """Refuse any model endpoint that is not known to be free."""
    if provider in _FREE_PROVIDERS:
        return
    if not base_url or not base_url.strip():
        raise WouldCostMoney(
            f"provider {provider!r} has no LLM_BASE_URL, so there is no way to tell "
            f"whether it bills per token. Set it to a free endpoint "
            f"(https://api.groq.com/openai/v1) or use the github provider."
        )
    host = (urlparse(base_url.strip()).hostname or "").lower()
    if not host:
        raise WouldCostMoney(f"could not read a hostname out of LLM_BASE_URL={base_url!r}")
    if host in FREE_ENDPOINTS or host.endswith(".local"):
        return
    raise WouldCostMoney(
        f"{host} is not on the list of endpoints known to be free, so this run "
        f"could be billed per token. This project must never cost anything. If "
        f"{host} really is free, add it to FREE_ENDPOINTS in builder/cost.py "
        f"deliberately; do not let an unknown endpoint through by default."
    )


def preflight_actions() -> None:
    """Checks for the money GitHub could charge: metered minutes.

    Deliberately not the endpoint check. A run that never reaches a paid model
    cannot be billed by one, so that check lives at the point of spend -- inside
    the provider, on the line that makes the request.
    """
    check_visibility(os.environ.get("FORGE_REPO_VISIBILITY"))
    check_runner(os.environ.get("FORGE_RUNNER"))


def preflight(provider: str, env: dict[str, str] | None = None) -> None:
    """Run every check that stands between this job and somebody's credit card."""
    source = os.environ if env is None else env
    check_visibility(source.get("FORGE_REPO_VISIBILITY"))
    check_runner(source.get("FORGE_RUNNER"))
    check_endpoint(provider, source.get("LLM_BASE_URL"))
