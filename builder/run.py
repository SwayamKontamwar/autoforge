"""The autoforge orchestrator.

One invocation implements at most one backlog item:

1. pick the next open backlog task;
2. ask the configured model for a whole-file patch touching only app/ and tests/;
3. apply it and run the guardrail (ruff + import + pytest);
4. on success: mark the task done, log it, commit, and push;
   on failure: revert the code, log the failure, and still commit the log so the
   daily cadence and audit trail continue without ever shipping broken code.

Run ``python -m builder.run --provider mock --no-push`` to exercise it offline.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import inspect
import json
import keyword
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from builder import backlog, backlog_gen, cost, devlog, honesty
from builder.guardrail import GuardrailResult, count_tests
from builder.guardrail import run as run_guardrail
from builder.llm import DoesNotFit, Patch, ProviderError, get_provider

ALLOWED_PREFIXES = ("app/", "tests/")
# The prompt and the answer are metered against one shared allowance, so every
# character spent describing the repository is a character the model cannot spend
# writing code. At 16000 the context took 62% of the free tier's budget and left
# barely enough to rewrite one medium file. Context is ranked by relevance, so the
# lost tail is the least useful part of it.
CONTEXT_BUDGET = 9000
# The file listing is capped separately: it grows with every task forever, while
# file bodies are bounded by whatever fits after it.
LISTING_BUDGET = 2000
REPLENISH_THRESHOLD = 40
REPLENISH_BATCH = 80
# Re-log an ongoing outage this often. Comfortably inside GitHub's 60-day
# inactivity window, which is when it disables scheduled workflows.
HEARTBEAT_DAYS = 14

# How long a provider may stay down before the run starts failing red. Short outages
# are normal on a free tier and must not cry wolf; a revoked key is forever, and the
# only thing standing between that and years of silence is a workflow that goes red.
OUTAGE_GRACE_DAYS = 3


def _git(repo_root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=check,
    )


def _is_clean(repo_root: Path) -> bool:
    return _git(repo_root, "status", "--porcelain").stdout.strip() == ""


def _sanitize_state(loaded: dict) -> dict:
    """Force a committed state file into the shape the rest of the run assumes.

    Guarding the top-level type is not enough. Every value in here is read back
    later -- attempt counts get ``int()`` called on them and incremented, stored
    failures get ``.pop()`` called on them -- and a value of the wrong type raises
    somewhere deep in the run rather than here. Because this file is committed,
    that is not a one-off crash: the same bad file is restored on every future
    checkout, so the loop crashes identically forever with nobody watching.

    Anything that is not the expected shape is dropped rather than repaired. A
    dropped attempt count costs a few extra retries of one task. A wedged loop
    costs the whole experiment.
    """
    clean: dict = {}
    for key, value in loaded.items():
        if key == _FAILURES_KEY:
            if isinstance(value, dict):
                clean[key] = {k: v for k, v in value.items() if isinstance(k, str)}
        elif key == _OUTAGE_KEY:
            if isinstance(value, str):
                clean[key] = value
        elif key == _BUILDER_KEY:
            if isinstance(value, str):
                clean[key] = value
        elif isinstance(value, bool):
            continue  # bool is an int in Python, but an attempt count is not a flag
        elif isinstance(value, int):
            clean[key] = value
        elif isinstance(value, float) and value.is_integer():
            clean[key] = int(value)
    return clean


def _load_state(state_path: Path) -> dict:
    """Read attempt state, treating anything unreadable as "no state yet".

    This file is committed, so a damaged one is not a transient glitch: it would be
    restored on every future checkout and crash the run before any work could start,
    with no way for the loop to repair itself. Losing attempt counts costs a few
    extra retries; refusing to start costs the entire experiment. Note that a
    truncated write can split a multi-byte character, so decoding fails before JSON
    parsing even begins.
    """
    if not state_path.exists():
        return {}
    try:
        loaded = json.loads(state_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError, OSError):
        return {}
    return _sanitize_state(loaded) if isinstance(loaded, dict) else {}


def _save_state(state_path: Path, state: dict) -> None:
    """Write attempt state atomically, so a killed run cannot truncate it.

    ``os.replace`` is atomic on POSIX and Windows: readers see either the old file
    or the new one, never a half-written one. Writing in place would leave a
    truncated file if the runner were killed mid-write.
    """
    state_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(state, indent=2, sort_keys=True) + "\n"
    tmp = state_path.with_name(state_path.name + ".tmp")
    tmp.write_text(payload, encoding="utf-8")
    os.replace(tmp, state_path)


# Attempt counts live in the state dict keyed by task text; failures hang off this
# reserved key so both survive in one committed file.
_FAILURES_KEY = "__last_failures__"
_OUTAGE_KEY = "__outage_since__"
_BUILDER_KEY = "__builder_fingerprint__"


def _builder_fingerprint(repo_root: Path) -> str:
    """Hash the builder's own source, so a change to it is detectable.

    Only the machinery is hashed, not the product being built. ``app/`` and
    ``tests/`` change on almost every run, and treating those as a builder change
    would reset attempt counts constantly and defeat the skip threshold entirely.
    """
    digest = hashlib.sha256()
    found = False
    builder_dir = repo_root / "builder"
    try:
        sources = sorted(builder_dir.glob("*.py"), key=lambda p: p.name)
    except OSError:
        return ""
    for path in sources:
        try:
            digest.update(path.name.encode("utf-8"))
            digest.update(path.read_bytes())
        except OSError:
            continue
        found = True
    # No readable sources means "cannot tell", which must not be mistaken for a
    # real fingerprint -- the empty hash is a stable value and would otherwise look
    # like a genuine builder that then "changed" the moment sources appeared.
    return digest.hexdigest()[:16] if found else ""


def _refresh_stale_evidence(repo_root: Path, backlog_path: Path, state: dict) -> list[str]:
    """Clear failures and reopen retirements once the builder itself has changed.

    Three failures normally mean the task is the problem. But when the builder
    changes, that count stops being evidence about the task -- it may only ever
    have been evidence about a bug that is now gone. Both tasks retired in this
    repository were killed by a keyword bug in the builder, not by anything about
    the tasks, and both were solvable throughout.

    Tying revival to a fingerprint rather than a timer is what keeps this from
    becoming an infinite retry loop: a genuinely impossible task is retried only
    when a human has actually changed the machinery, which is rare and is exactly
    the moment its previous verdict became untrustworthy.
    """
    current = _builder_fingerprint(repo_root)
    if not current:
        return []
    previous = state.get(_BUILDER_KEY)
    state[_BUILDER_KEY] = current
    if previous is None or previous == current:
        return []
    state[_FAILURES_KEY] = {}
    for key in [k for k in state if not k.startswith("__")]:
        state.pop(key, None)
    try:
        return backlog.revive_skipped(backlog_path)
    except OSError:
        return []


def _remember_failure(state: dict, task: str, log: str) -> None:
    state.setdefault(_FAILURES_KEY, {})[task] = _tail(log)


def _forget_failure(state: dict, task: str) -> None:
    state.get(_FAILURES_KEY, {}).pop(task, None)


def _close_task_state(state: dict, task: str) -> None:
    """Drop everything remembered about a task that will never be attempted again.

    Both the attempt count and the stored traceback are only useful while a task is
    still live. Left behind, they accumulate one entry per finished task for the
    life of the repository — a file that grows forever in a project designed to run
    for years.
    """
    state.pop(task, None)
    _forget_failure(state, task)


def _previous_failure(state: dict, task: str) -> str:
    failures = state.get(_FAILURES_KEY)
    return failures.get(task, "") if isinstance(failures, dict) else ""


def _with_failure_note(context: str, failure: str) -> str:
    """Append the last guardrail failure so a retry is not a blind repeat.

    Without this the model receives a byte-identical prompt on every attempt and
    reliably makes the same mistake until the task is skipped — work abandoned one
    small fix away from passing. Handing back the traceback is what turns three
    wasted attempts into a correction.
    """
    return (
        f"{context}\n\n"
        "## Your previous attempt at this task failed\n\n"
        "You have already tried this task once. The patch was reverted because the "
        "guardrail failed with the output below. Read it carefully and fix the cause; "
        "do not submit the same patch again. Note that a change to one model or "
        "function often requires updating the others that use it.\n\n"
        f"```\n{failure}\n```\n"
    )


# Words that appear in nearly every backlog item and so carry no signal about
# which files a task touches.
_STOPWORDS = frozenset(
    """a an and the to for of in on with add adds added support use using make
    ensure that this it its into from when where new create creates return returns
    handle handles allow allows so is are be given then also each any all app
    tests test py module code function class method value values""".split()
)


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in _STOPWORDS}


# Ranking reads file bodies, so it has to stay bounded: the whole tree is scored on
# every run, forever. Only the head of each file is scored, which is where imports
# and definitions live and so where the subject of a file is most visible.
_RANK_READ_LIMIT = 8000


def _relevance_text(path: Path) -> str:
    """The head of a file, lowercased, or empty if it cannot be read.

    Ranking is a convenience: an unreadable file must fall to the bottom of the
    order rather than end the run, exactly as the body loop already treats one.
    """
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            return handle.read(_RANK_READ_LIMIT).lower()
    except (OSError, ValueError):
        return ""


def _is_machinery(text: str) -> bool:
    """Whether a file under tests/ is about the builder rather than the product.

    Every task in the backlog is a task about the application. The tests that
    cover the builder are not: the model is never asked to change them and is
    refused if it tries. They are still ordinary files under ``tests/``, so they
    compete for context on equal terms and, being much larger than application
    code, they win -- the machinery tests outweigh the application's own tests
    roughly six to one, and a single one of them is three times the entire budget.

    This is the part that gets worse on its own. Every fix to the builder adds to
    its tests, so the harder the machinery is hardened the less room is left to
    show the model the code it is supposed to be writing. Left alone it ends with
    a context made almost entirely of files the model must not touch. Demoting
    rather than dropping them keeps the door open if a task ever genuinely names
    one.
    """
    return "from builder" in text or "import builder" in text


def _content_hits(text: str, task_words: set[str]) -> int:
    """How many distinct task words this file mentions.

    Substring rather than token matching, because the words a task uses and the
    identifiers a file uses differ by exactly the affixes that token matching
    treats as a mismatch: a task saying "timestamps" is about a file saying
    "timestamp", and one saying "UTC" is about a file calling ``utcnow()``.
    Counting distinct words rather than occurrences stops one repeated identifier
    from outscoring a file that genuinely covers the subject.
    """
    if not text:
        return 0
    return sum(1 for word in task_words if len(word) >= 3 and word in text)


def _ranked_files(repo_root: Path, task_text: str) -> list[Path]:
    """Order source files by how likely they are to matter to this task.

    Alphabetical order is fine for ten files and useless for a thousand: the same
    handful of files that happen to sort first would be sent every single time,
    the task's actual subject would never be visible, and no test file would ever
    be included at all because ``app/`` sorts before ``tests/``. This repository is
    supposed to keep working after years of daily commits, so file selection has to
    stay useful as the tree grows rather than degrade into an alphabetical prefix.

    Names alone are not enough to do that. Most tasks share no word with any
    filename, so every file scores zero and the order collapses back to the
    alphabetical prefix this function exists to avoid -- while a file whose name
    happens to catch an incidental word ("ISO 8601 *strings*") is promoted over the
    one that actually has to change. That is not a ranking that merely reads oddly:
    the file the task is about falls past the context budget, and the model is asked
    to edit code it was never shown. It answers by patching whatever it *can* see,
    the guardrail rejects the half-change, and after three tries the task is retired
    as impossible. Scoring what is inside a file, not just what it is called, is what
    keeps that from happening quietly for years.
    """
    tracked = sorted(
        p
        for prefix in ALLOWED_PREFIXES
        for p in (repo_root / prefix.rstrip("/")).rglob("*.py")
        # A directory can be named "*.py"; reading one raises and kills the run.
        if p.is_file()
    )
    task_words = _words(task_text)

    def rank(path: Path) -> tuple[int, int, int, str]:
        rel = str(path.relative_to(repo_root))
        named = 0 if rel and rel in task_text else 1
        text = _relevance_text(path)
        name_overlap = len(_words(rel.replace("/", " ").replace("_", " ")) & task_words)
        # A filename match is a deliberate signal and a body match is a
        # circumstantial one, so names still lead -- they just no longer decide it
        # alone when nothing matches by name at all.
        score = 2 * name_overlap + _content_hits(text, task_words)
        return (named, 1 if _is_machinery(text) else 0, -score, rel)

    return sorted(tracked, key=rank)


def _build_context(repo_root: Path, task_text: str = "") -> str:
    ranked = _ranked_files(repo_root, task_text)

    # The listing has to be capped too. Left unbounded it outgrows the model's
    # context and the free tier's per-minute token allowance on its own — measured
    # at ~141k characters for 6k files — at which point every future run fails on
    # size alone and the repository stops building itself for good.
    shown: list[str] = []
    listing_used = 0
    for path in ranked:
        rel = str(path.relative_to(repo_root))
        if listing_used + len(rel) + 1 > LISTING_BUDGET:
            break
        shown.append(rel)
        listing_used += len(rel) + 1
    hidden = len(ranked) - len(shown)
    listing = "\n".join(shown)
    if hidden > 0:
        listing += f"\n... and {hidden} more files (most relevant to this task shown first)"
    sections = [f"Files:\n{listing}\n"]

    budget = CONTEXT_BUDGET
    for path in ranked:
        rel = path.relative_to(repo_root)
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            # Context is a convenience; an unreadable file must not end the run.
            continue
        block = f"\n--- {rel} ---\n{content}"
        if len(block) > budget:
            block = block[:budget] + "\n... (truncated)"
        budget -= len(block)
        sections.append(block)
        if budget <= 0:
            break
    return "\n".join(sections)


def _reject_reason(patch: Patch) -> str | None:
    # A task may only be closed by work that exists. Both response parsers already
    # refuse an empty file list, but the invariant belongs where completion is
    # decided rather than only where responses are parsed: a future provider or
    # format would otherwise reopen the hole silently, and the symptom is the worst
    # kind -- tasks ticked off with nothing written.
    if not patch.files:
        return "the patch contained no files"
    for file in patch.files:
        norm = os.path.normpath(file.path).replace(os.sep, "/")
        if norm.startswith("/") or norm.startswith(".."):
            return f"path escapes the repository: {file.path}"
        if not norm.startswith(ALLOWED_PREFIXES):
            return f"path outside app/ or tests/: {file.path}"
        # "app/router.py/user.py" creates a *directory* named router.py. It passes
        # every check and commits, and from then on every prompt build walks the tree
        # and tries to read that directory as a file, which crashes the run before any
        # attempt is recorded -- the same task, forever.
        if any(part.endswith(".py") for part in norm.split("/")[:-1]):
            return f"path nests inside a module file: {file.path}"
    # A patch may not rewrite the machinery that is about to judge it.
    return honesty.rigged_verdict_reason(patch.files)


def _apply(repo_root: Path, patch: Patch) -> None:
    for file in patch.files:
        target = repo_root / file.path
        target.parent.mkdir(parents=True, exist_ok=True)
        content = file.content if file.content.endswith("\n") else file.content + "\n"
        target.write_text(content, encoding="utf-8")


def _retired_kwarg_rewrite() -> tuple[str, str] | None:
    """Return the keyword swap the installed client needs, or None if it needs none.

    The model cannot stop writing ``allow_redirects=``. It is the ``requests``
    spelling, it is all over the training data, and the installed ``httpx`` deleted
    it. Stating the correct name in the prompt did not work: the model wrote the
    dead keyword again on the very next run, with the previous ``TypeError`` quoted
    back to it as feedback. Left alone this burns all three attempts and retires a
    task permanently, over and over, for years.

    So it is repaired mechanically instead of asked for politely. The swap is
    derived from the installed signature rather than hard-coded, so if a future
    version restores the old name -- or renames it again -- this stops rewriting
    instead of silently corrupting working code.
    """
    try:
        from fastapi.testclient import TestClient

        params = inspect.signature(TestClient.get).parameters
    except Exception:
        return None
    if "follow_redirects" in params and "allow_redirects" not in params:
        return ("allow_redirects", "follow_redirects")
    return None


def _fix_retired_kwargs(repo_root: Path, patch: Patch) -> list[str]:
    """Swap the dead keyword in generated tests. Returns the files changed."""
    swap = _retired_kwarg_rewrite()
    if swap is None:
        return []
    old, new = swap
    pattern = re.compile(rf"\b{re.escape(old)}(\s*=)")
    changed = []
    for file in patch.files:
        # Only tests call the client, and only tests may import it at all, so a
        # rewrite can never reach production semantics.
        if not file.path.replace("\\", "/").startswith("tests/"):
            continue
        target = repo_root / file.path
        try:
            text = target.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        fixed = pattern.sub(rf"{new}\1", text)
        if fixed != text:
            try:
                target.write_text(fixed, encoding="utf-8")
            except OSError:
                continue
            changed.append(file.path)
    return changed


_AMBIGUOUS_NAMES = frozenset({"l", "I", "O"})
_RENAME_CANDIDATES = ("item", "value", "entry", "element", "obj")


def _lambda_args(node: ast.Lambda) -> list[ast.arg]:
    args = node.args
    every = [*args.posonlyargs, *args.args, *args.kwonlyargs]
    if args.vararg is not None:
        every.append(args.vararg)
    if args.kwarg is not None:
        every.append(args.kwarg)
    return every


def _rebinds(body: ast.expr, name: str) -> bool:
    """True if anything inside a lambda body binds ``name`` again.

    If it does, the occurrences of ``name`` in that body no longer all refer to the
    lambda's own parameter, so a blanket rename would be wrong. Rather than reason
    about which occurrence belongs to which scope, this bails out entirely.
    """
    for sub in ast.walk(body):
        if isinstance(sub, ast.Lambda) and any(a.arg == name for a in _lambda_args(sub)):
            return True
        if isinstance(sub, ast.ListComp | ast.SetComp | ast.DictComp | ast.GeneratorExp):
            for gen in sub.generators:
                for target in ast.walk(gen.target):
                    if isinstance(target, ast.Name) and target.id == name:
                        return True
        if (
            isinstance(sub, ast.NamedExpr)
            and isinstance(sub.target, ast.Name)
            and sub.target.id == name
        ):
            return True
    return False


def _free_name(taken: set[str]) -> str | None:
    for base in _RENAME_CANDIDATES:
        if base not in taken and not keyword.iskeyword(base):
            return base
    for suffix in range(2, 100):
        for base in _RENAME_CANDIDATES:
            candidate = f"{base}{suffix}"
            if candidate not in taken:
                return candidate
    return None


def _rename_ambiguous_lambda_params(source: str) -> str | None:
    """Rename E741 lambda parameters. Returns new source, or None if nothing to do.

    ``ruff`` cannot fix E741 itself -- renaming a binding needs scope analysis it
    does not do -- so this does it, and only for the one case where it is provably
    safe: a lambda parameter. Its scope is exactly the lambda body, so it cannot be
    a global, cannot leak into surrounding code, and cannot collide with anything
    outside. ``for`` targets and assignments are deliberately left alone; they leak.

    The rewrite is done by splicing exact source positions rather than
    ``ast.unparse``, which would reformat the whole file and could introduce fresh
    lint errors of its own. The splice is then proven correct by comparing the
    result's AST against the same rename applied directly to the original tree.

    Every step walks an attacker-shaped tree, so the whole thing is guarded: deeply
    nested input blows the stack inside ``ast.walk`` and ``ast.dump`` as readily as
    inside ``ast.parse``. A cosmetic repair must never be the thing that kills a run.
    """
    try:
        return _rename_ambiguous_lambda_params_unguarded(source)
    except (SyntaxError, ValueError, RecursionError, MemoryError):
        return None


def _rename_ambiguous_lambda_params_unguarded(source: str) -> str | None:
    tree = ast.parse(source)

    taken = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    taken |= {a.arg for n in ast.walk(tree) if isinstance(n, ast.Lambda) for a in _lambda_args(n)}
    taken |= {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef | ast.ClassDef)}

    renames: list[tuple[ast.arg, list[ast.Name], str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Lambda):
            continue
        for arg in _lambda_args(node):
            if arg.arg not in _AMBIGUOUS_NAMES or _rebinds(node.body, arg.arg):
                continue
            new = _free_name(taken)
            if new is None:
                continue
            taken.add(new)
            uses = [n for n in ast.walk(node.body) if isinstance(n, ast.Name) and n.id == arg.arg]
            renames.append((arg, uses, new))
    if not renames:
        return None

    edits: list[tuple[int, int, int, str]] = []
    for arg, uses, new in renames:
        for spot in (arg, *uses):
            if spot.end_lineno != spot.lineno or spot.end_col_offset is None:
                return None
            edits.append((spot.lineno, spot.col_offset, spot.end_col_offset, new))

    # col_offset is a utf-8 byte offset, not a character index, so splice in bytes.
    lines = source.splitlines(keepends=True)
    by_line: dict[int, list[tuple[int, int, str]]] = {}
    for lineno, start, end, new in edits:
        if not 1 <= lineno <= len(lines):
            return None
        by_line.setdefault(lineno, []).append((start, end, new))
    for lineno, spots in by_line.items():
        raw = lines[lineno - 1].encode("utf-8")
        for start, end, new in sorted(spots, reverse=True):
            raw = raw[:start] + new.encode("utf-8") + raw[end:]
        lines[lineno - 1] = raw.decode("utf-8")
    rewritten = "".join(lines)

    # Prove the text surgery did exactly the intended rename and nothing else.
    for arg, uses, new in renames:
        arg.arg = new
        for use in uses:
            use.id = new
    try:
        actual = ast.parse(rewritten)
    except (SyntaxError, ValueError, RecursionError, MemoryError):
        return None
    if ast.dump(actual) != ast.dump(tree):
        return None
    return rewritten


def _fix_ambiguous_names(repo_root: Path, patch: Patch) -> list[str]:
    """Rename ambiguous lambda parameters in generated code. Returns files changed.

    ``lambda l: l.hits`` is an ingrained Python habit and the model writes it
    constantly -- it caused a third of all guardrail failures. Every one was real,
    working code rejected purely on the name of a throwaway variable, burning an
    attempt each time until the task retired permanently. Telling the model not to
    was already proven useless on the httpx keyword, so this is repaired instead.
    """
    changed = []
    for file in patch.files:
        if not file.path.endswith(".py"):
            continue
        target = repo_root / file.path
        try:
            source = target.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        fixed = _rename_ambiguous_lambda_params(source)
        if fixed is None or fixed == source:
            continue
        try:
            target.write_text(fixed, encoding="utf-8")
        except OSError:
            continue
        changed.append(file.path)
    return changed


def _autofix(repo_root: Path, patch: Patch) -> None:
    """Auto-repair safe, trivial lint issues in the generated files before judging.

    Operates only on the exact files the model wrote (already proven in-bounds), so
    nothing else in the tree is touched. Logic mistakes still fail the guardrail's
    tests; this only fixes style the model got slightly wrong (import order, unused
    imports, whitespace), turning otherwise-good work into a clean commit instead of
    a needless revert.
    """
    fixed = _fix_retired_kwargs(repo_root, patch)
    if fixed:
        print(f"rewrote a retired httpx keyword in: {', '.join(fixed)}")
    renamed = _fix_ambiguous_names(repo_root, patch)
    if renamed:
        print(f"renamed an ambiguous lambda parameter in: {', '.join(renamed)}")
    paths = [file.path for file in patch.files if (repo_root / file.path).exists()]
    if not paths:
        return
    for tool in (["check", "--fix", "--quiet"], ["format", "--quiet"]):
        subprocess.run(
            [sys.executable, "-m", "ruff", *tool, *paths],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )


def _revert(repo_root: Path) -> None:
    for prefix in ALLOWED_PREFIXES:
        _git(repo_root, "checkout", "--", prefix, check=False)
        _git(repo_root, "clean", "-fd", prefix, check=False)


# Written immediately before a patch touches the disk and removed once the patch
# has been judged. Its presence means a run died in between.
_INFLIGHT_NAME = "inflight"


def _inflight_path(repo_root: Path) -> Path:
    return repo_root / ".forge" / _INFLIGHT_NAME


def _begin_inflight(repo_root: Path) -> None:
    path = _inflight_path(repo_root)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("a patch is being applied and judged\n", encoding="utf-8")
    except OSError:
        pass  # Losing the marker costs cleanup later; failing here costs the run.


def _end_inflight(repo_root: Path) -> None:
    try:
        _inflight_path(repo_root).unlink(missing_ok=True)
    except OSError:
        pass


def _recover_interrupted_run(repo_root: Path) -> bool:
    """Undo a patch left on disk by a run that was killed while judging it.

    On a GitHub runner this never fires -- the machine is destroyed and the next
    run checks out fresh. It matters for the local ``cron``/``launchd`` setup the
    README suggests, where the checkout persists. There, a run killed between
    writing the patch and judging it leaves modified files behind, every later run
    sees a dirty tree and aborts, and the loop is wedged until a human notices.
    Silence is exactly how that gets missed.

    Only the marker authorises this. Without it a dirty tree is somebody's work in
    progress and is still refused, because cleaning that up would be worse than
    stopping.
    """
    if not _inflight_path(repo_root).exists():
        return False
    _revert(repo_root)
    _end_inflight(repo_root)
    return True


_IDENTITY = (
    "-c",
    "user.name=autoforge-bot",
    "-c",
    "user.email=autoforge-bot@users.noreply.github.com",
)


def _push(repo_root: Path, attempts: int = 3) -> bool:
    """Push, rebasing onto the remote if it moved under us.

    The bot commits work that has already passed the guardrail, so losing it to a
    rejected push is the worst outcome available: the run fails red, the task is
    marked done locally, and the code is thrown away. A human pushing between this
    job's checkout and its push is enough to trigger it. Rebase and retry instead,
    and if the rebase genuinely conflicts, fail loudly rather than force-pushing
    over someone else's commit.
    """
    branch = _git(repo_root, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    for attempt in range(attempts):
        if _git(repo_root, "push", "origin", "HEAD", check=False).returncode == 0:
            print("pushed")
            return True
        if attempt == attempts - 1:
            break
        print("push rejected; remote moved, rebasing and retrying")
        pull = _git(repo_root, *_IDENTITY, "pull", "--rebase", "origin", branch, check=False)
        if pull.returncode != 0:
            conflicted = any(
                (repo_root / ".git" / d).exists() for d in ("rebase-merge", "rebase-apply")
            )
            _git(repo_root, "rebase", "--abort", check=False)
            why = "conflicted" if conflicted else "could not run"
            print(
                f"rebase onto the remote {why}; not force-pushing\n{pull.stderr.strip()}",
                file=sys.stderr,
            )
            return False
    print("could not push after retrying", file=sys.stderr)
    return False


def _commit(repo_root: Path, message: str, push: bool) -> bool:
    """Commit and publish. False means the work exists locally but not on the remote.

    A runner is thrown away when the job ends, so a commit that is not pushed is a
    commit that never happened. Worse, an unpushed run leaves no repository activity,
    and GitHub disables a schedule after sixty days without any -- so a push that
    silently fails does not just lose one run, it eventually stops the loop entirely.
    The caller turns this into a non-zero exit so the failure is visible.
    """
    _end_inflight(repo_root)
    _git(repo_root, "add", "-A")
    if _git(repo_root, "diff", "--cached", "--quiet", check=False).returncode == 0:
        print("nothing to commit")
        return True
    _git(repo_root, *_IDENTITY, "commit", "-m", message)
    print(f"committed: {message}")
    if push:
        return _push(repo_root)
    return True


def _ask(provider_name: str, repo_root: Path, state: dict, task: str) -> Patch:
    """Get a patch from the provider, turning the unknown into a known outage.

    Everything downstream of this call is crash-proof; this call was not. It reaches
    the network through urllib, ssl and http.client, and those raise things not
    listed anywhere here -- a socket timeout comes straight out of urllib rather than
    wrapped in a URLError, which is how this was found. An exception escaping here
    lands in the one window the loop cannot absorb: after the task is chosen and
    before the attempt is recorded, so the tree stays dirty, the count never rises,
    and the same task is chosen and crashes again on every future run, forever.

    Calling the unknown an outage is only honest because an outage is no longer
    quiet: if it keeps happening, the run starts failing red after OUTAGE_GRACE_DAYS.
    """
    try:
        provider = get_provider(provider_name)
        context = _build_context(repo_root, task)
        prior_failure = _previous_failure(state, task)
        if prior_failure:
            print("retrying with the previous guardrail failure as feedback")
            context = _with_failure_note(context, prior_failure)
        return provider.generate(task, context)
    except (ProviderError, DoesNotFit):
        raise
    except Exception as exc:
        raise ProviderError(f"{type(exc).__name__}: {exc}") from exc


def _outage_started(state: dict) -> datetime:
    """When the current provider outage began, recorded across runs.

    Taken from the committed state rather than the git log because the workflow
    checks out at depth one: only the newest commit is visible, so history cannot
    say how long this has been going on. The stamp is written with the "blocked"
    commit and read for free on every quiet run after it.
    """
    raw = state.get(_OUTAGE_KEY)
    if isinstance(raw, str):
        try:
            return datetime.fromisoformat(raw)
        except ValueError:
            pass
    return datetime.now(timezone.utc)


def _outage_already_logged(repo_root: Path, provider: str) -> bool:
    """True when an outage for ``provider`` is already recorded and still fresh.

    Backlog replenishment is bookkeeping, not progress, so it is skipped when looking
    back. This lets the loop log a provider outage once and then stay silent while it
    lasts, instead of appending an identical "blocked" commit on every scheduled run.

    Silence is deliberately not permanent: GitHub disables scheduled workflows after
    60 days without repository activity, so a long outage that produced no commits at
    all would quietly kill the schedule and end the experiment for good. After
    ``HEARTBEAT_DAYS`` the outage is re-logged, which keeps the repository active and
    the cron alive while still cutting three notes a day down to roughly two a month.
    """
    result = _git(repo_root, "log", "--pretty=%cI%x09%s", check=False)
    if result.returncode != 0:
        return False
    marker = f"forge: log blocked task ({provider} unavailable)"
    for line in result.stdout.splitlines():
        stamp, _, subject = line.partition("\t")
        subject = subject.strip()
        if not subject or subject.startswith("forge: replenish backlog"):
            continue
        if subject != marker:
            return False
        try:
            logged_at = datetime.fromisoformat(stamp.strip())
        except ValueError:
            return True
        age = datetime.now(timezone.utc) - logged_at
        return age < timedelta(days=HEARTBEAT_DAYS)
    return False


def _mark_done(backlog_path: Path, task: backlog.Task, note: str | None = None) -> None:
    """Tick a task off, tolerating a backlog that no longer holds it open.

    ``mark_done`` refuses a stale index rather than corrupting a line. Reaching that
    point means the task is not open any more, so there is nothing left to record and
    the run should finish normally instead of stranding itself.
    """
    try:
        backlog.mark_done(backlog_path, task.index, note=note, expect=task.text)
    except ValueError as exc:
        print(f"could not tick the task off: {exc}", file=sys.stderr)


def _restore_outside_patch_area(repo_root: Path) -> None:
    """Undo whatever a check wrote outside ``app/`` and ``tests/``.

    The guardrail does not merely inspect generated code, it *executes* it: ruff, an
    import of the app, and pytest all run with the repository as their working
    directory. A patch confined to ``tests/`` can therefore still write to
    ``BACKLOG.md``, ``DEVLOG.md``, ``.forge/state.json`` or the repository root --
    paths that the revert does not restore and that ``git add -A`` does commit.

    Reproduced before this existed: a test that rewrote ``BACKLOG.md`` and passed
    took the backlog from 1032 open tasks to none, committed it, and shifted the line
    numbering so the wrong task was marked done. There is no way back from that once
    it reaches the remote, so it is undone after every check rather than trusted not
    to happen.
    """
    _git(repo_root, "checkout", "--", ".", ":(exclude)app", ":(exclude)tests", check=False)
    listed = _git(repo_root, "ls-files", "--others", "--exclude-standard", check=False)
    if listed.returncode != 0:
        return
    for line in listed.stdout.splitlines():
        rel = line.strip()
        if not rel or rel.startswith(("app/", "tests/")):
            continue
        target = repo_root / rel
        if target.is_file():
            target.unlink()


def _patch_changed_anything(repo_root: Path, patch: Patch) -> bool:
    """True when the patch's own files differ from HEAD.

    Scoped to the patch rather than the whole tree on purpose: asking "is anything
    dirty?" would answer yes for unrelated dirt and quietly stop detecting a patch
    that did nothing. Git is the judge rather than a content comparison so that
    whitespace and line-ending normalisation are counted the way a commit would.
    """
    paths = [file.path for file in patch.files]
    if not paths:
        return False
    result = _git(repo_root, "status", "--porcelain", "--", *paths, check=False)
    if result.returncode != 0:
        return True
    return bool(result.stdout.strip())


def _safe_count_tests(repo_root: Path) -> int:
    """``count_tests`` but never fatal; -1 means "could not measure"."""
    try:
        return count_tests(repo_root)
    except Exception:
        return -1
    finally:
        # Collection imports every test module, so it runs repository code too.
        _restore_outside_patch_area(repo_root)


def _judge(repo_root: Path, patch: Patch) -> GuardrailResult:
    """Apply the patch and judge it, converting any crash into a failed attempt.

    The model controls file paths and file contents, so applying a patch can raise
    in ways no allowlist anticipates: writing a module where a package directory
    already exists, a name the filesystem rejects, a path that is too long. Left
    uncaught, the exception escapes before the revert and before the attempt is
    recorded, so the tree stays dirty and the task keeps its old attempt count --
    and is therefore chosen again, and crashes again, on every future run.

    Treating it as an ordinary guardrail failure keeps the loop moving: the patch is
    reverted, the attempt counts toward the skip threshold, and the error text goes
    back to the model as feedback for its next try.
    """
    _begin_inflight(repo_root)
    try:
        _apply(repo_root, patch)
        # Judged before _autofix, not after: reformatting a verbatim copy of an
        # existing file is itself a change, so autofixing first would disguise a
        # patch that did nothing as a patch that did something.
        if not _patch_changed_anything(repo_root, patch):
            # The tree was clean before the patch, so writing it and changing nothing
            # means the model returned content identical to what is already on disk.
            # The guardrail would pass on an unchanged repository and the task would
            # be ticked off without a line of work behind it.
            return GuardrailResult(
                ok=False,
                log=(
                    "$ apply patch\nThe patch left the repository unchanged: every "
                    "file matches what is already on disk. Implement the task, or say "
                    "what is missing -- do not return existing files verbatim.\n"
                ),
            )
        _autofix(repo_root, patch)
        return run_guardrail(repo_root)
    except Exception as exc:
        paths = ", ".join(file.path for file in patch.files) or "(none)"
        return GuardrailResult(
            ok=False,
            log=(
                f"$ apply patch\n{type(exc).__name__}: {exc}\n"
                f"Files in this patch: {paths}\n"
                "The patch could not be written to disk. Check that every path is a "
                "plain file that does not collide with an existing directory.\n"
            ),
        )
    finally:
        _restore_outside_patch_area(repo_root)


def _baseline(repo_root: Path) -> GuardrailResult:
    """Guardrail on the reverted tree; a crash here is an environment fault."""
    try:
        return run_guardrail(repo_root)
    except Exception as exc:
        return GuardrailResult(ok=False, log=f"$ baseline guardrail\n{type(exc).__name__}: {exc}\n")
    finally:
        _restore_outside_patch_area(repo_root)


def _tail(log: str, limit: int = 2000) -> str:
    return log if len(log) <= limit else "... (truncated)\n" + log[-limit:]


def _unusable_layout(repo_root: Path, backlog_path: Path, devlog_path: Path) -> str:
    """Explain why the repository cannot be worked on, or return "" if it can.

    Every one of these used to surface as a bare traceback -- FileNotFoundError,
    IsADirectoryError, FileExistsError -- from somewhere in the middle of the run.
    A traceback in a log nobody reads is the same as silence. These are all states
    the loop genuinely cannot fix by itself, so the right answer is to stop and say
    which file is wrong, not to crash describing the line that tripped over it.
    """
    if not backlog_path.exists():
        return f"{backlog_path.name} is missing; there is no work to read"
    if not backlog_path.is_file():
        return f"{backlog_path.name} is not a regular file"
    forge_dir = repo_root / ".forge"
    if forge_dir.exists() and not forge_dir.is_dir():
        return ".forge exists but is not a directory, so run state cannot be stored"
    if devlog_path.exists() and not devlog_path.is_file():
        return f"{devlog_path.name} is not a regular file"
    # Every reader of these files decodes them as UTF-8. One invalid byte raises
    # UnicodeDecodeError from whichever reader happens to run first -- and because
    # both files are committed, the same bytes come back on every future checkout,
    # so the loop dies at exactly the same place forever with nobody watching.
    # Refusing here turns a permanent traceback into one sentence naming the file.
    for path in (backlog_path, devlog_path):
        if not path.is_file():
            continue
        try:
            path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return f"{path.name} is not valid UTF-8 text, so its contents cannot be read"
        except OSError as exc:
            return f"{path.name} cannot be read ({exc.strerror or exc})"
    # Reading is not enough: every run appends to DEVLOG.md, rewrites BACKLOG.md
    # and writes .forge/state.json. A read-only file or a full disk surfaces as a
    # bare PermissionError/OSError from whichever write happens first, after the
    # model has already been called and the work done. Checking up front costs
    # nothing and turns a traceback into a sentence.
    #
    # Existing files are probed by opening for append, which writes nothing and
    # creates nothing. Directories are probed with os.access rather than by
    # touching a file, because a probe file is one SIGKILL away from being left
    # behind and swept into the next commit by "git add -A".
    for path in (backlog_path, devlog_path, repo_root):
        try:
            if path.is_dir():
                if not os.access(path, os.W_OK | os.X_OK):
                    return f"{path.name} is not writable"
            elif path.exists():
                with path.open("a", encoding="utf-8"):
                    pass
            elif not os.access(path.parent, os.W_OK | os.X_OK):
                return f"{path.name} cannot be created; its directory is not writable"
        except OSError as exc:
            return f"{path.name} is not writable ({exc.strerror or exc})"
    return ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the next backlog item.")
    parser.add_argument("--provider", default=os.getenv("LLM_PROVIDER", "github"))
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--backlog", default="BACKLOG.md")
    parser.add_argument("--devlog", default="DEVLOG.md")
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--no-push", action="store_true")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    backlog_path = repo_root / args.backlog
    devlog_path = repo_root / args.devlog
    state_path = repo_root / ".forge" / "state.json"
    push = not args.no_push

    # Before anything else, and before a single billable second is spent: this
    # experiment must cost nothing, forever, with nobody watching it.
    try:
        cost.preflight_actions()
    except cost.WouldCostMoney as exc:
        print(f"refusing to run: {exc}", file=sys.stderr)
        return 1

    unusable = _unusable_layout(repo_root, backlog_path, devlog_path)
    if unusable:
        print(f"cannot run here: {unusable}", file=sys.stderr)
        return 1

    if _recover_interrupted_run(repo_root):
        print("cleaned up a patch left behind by an interrupted run")

    if not _is_clean(repo_root):
        print("working tree is not clean; aborting", file=sys.stderr)
        return 1

    # Before anything reads task positions, since archiving renumbers the file.
    archived = backlog.archive_completed(backlog_path)
    if archived:
        rel = archived.relative_to(repo_root)
        devlog.append(
            devlog_path,
            "archived",
            f"moved completed backlog items to {rel}",
            "BACKLOG.md had grown past the size GitHub renders comfortably. Finished "
            "items now live in an archive that still counts against de-duplication, "
            "so nothing is lost and no task can come back a second time.",
        )
        print(f"archived completed backlog items to {rel}")
        _commit(repo_root, f"forge: archive completed backlog items to {rel}", push)

    if backlog.open_count(backlog_path) < REPLENISH_THRESHOLD:
        new_tasks = backlog_gen.replenish(repo_root, backlog_path, REPLENISH_BATCH)
        backlog.append_tasks(backlog_path, new_tasks, heading="Auto-generated follow-up work")
        devlog.append(
            devlog_path,
            "replenished",
            f"backlog running low; appended {len(new_tasks)} renewable tasks",
            "The curated backlog is nearly done, so the runtime generated more work "
            "from the toolkit it has already built. It never runs out.",
        )
        print(f"replenished backlog with {len(new_tasks)} tasks")
        _commit(repo_root, f"forge: replenish backlog (+{len(new_tasks)} tasks)", push)

    state = _load_state(state_path)
    # Do this before a task is chosen, so a revived task can be the one picked.
    revived = _refresh_stale_evidence(repo_root, backlog_path, state)
    if revived:
        _save_state(state_path, state)
        print(f"builder changed; reopened {len(revived)} previously retired task(s)")
        devlog.append(
            devlog_path,
            "revived",
            f"builder code changed; reopened {len(revived)} retired task(s)",
            "Tasks are retired after three failed attempts. When the builder itself "
            "changes, that count stops being evidence about the task, so retirement "
            "is revisited:\n\n"
            + "\n".join(f"- {t}" for t in revived),
        )
        _commit(repo_root, f"forge: reopen {len(revived)} task(s) after builder change", push)

    task = backlog.next_task(backlog_path)
    if task is None:
        print("backlog is empty; nothing to do")
        return 0
    print(f"next task: {task.text}")

    attempts = int(state.get(task.text, 0))

    try:
        patch = _ask(args.provider, repo_root, state, task.text)
    except DoesNotFit as exc:
        patch, truncated = Patch(files=[], summary=""), str(exc)
    except ProviderError as exc:
        # A provider outage is infrastructure trouble, not project progress. Record it
        # once, then stay quiet until it recovers: an outage lasting months must not
        # bury the dev log under thousands of identical "blocked" commits.
        #
        # Quiet is not the same as fine, though. Every one of these runs used to exit
        # 0, so a revoked key looked exactly like a healthy project: green ticks three
        # times a day, forever, building nothing. Nobody is watching the logs -- a red
        # run is the only signal that reaches the owner, so after a few days of the
        # same outage the run starts failing on purpose. The heartbeat commit still
        # goes out, because a repository with no activity has its schedule disabled
        # after sixty days and that would end the experiment for good.
        started = _outage_started(state)
        state[_OUTAGE_KEY] = started.isoformat()
        stalled = datetime.now(timezone.utc) - started >= timedelta(days=OUTAGE_GRACE_DAYS)
        if stalled:
            print(
                f"provider '{args.provider}' has been unavailable since "
                f"{started.date()}; no work is getting done",
                file=sys.stderr,
            )
        if _outage_already_logged(repo_root, args.provider):
            print(f"provider '{args.provider}' still unavailable ({exc}); already logged")
            return 1 if stalled else 0
        devlog.append(
            devlog_path,
            "blocked",
            task.text,
            f"Model provider '{args.provider}' was unavailable: {exc}. "
            "No code changed; will retry next run.",
        )
        _save_state(state_path, state)
        published = _commit(
            repo_root, f"forge: log blocked task ({args.provider} unavailable)", push
        )
        if not published:
            return 1
        return 1 if stalled else 0
    else:
        truncated = None

    # Every path through the outage branch returns, so reaching here means the
    # provider answered -- a cut-off answer is still an answer. Whatever outage was
    # running is over, and the clock must not carry over into the next one.
    state.pop(_OUTAGE_KEY, None)

    reason = truncated or _reject_reason(patch)
    if reason is not None:
        attempts += 1
        state[task.text] = attempts
        if attempts >= args.max_attempts:
            _mark_done(backlog_path, task, f"skipped after {attempts} out-of-bounds patches")
            status = "skipped"
            message = "forge: skip task after repeated out-of-bounds patches"
            detail = (
                f"Patch rejected: {reason}\n\n"
                f"Skipped after {attempts} out-of-bounds attempts so the backlog keeps moving."
            )
            _close_task_state(state, task.text)
        else:
            status = "rejected"
            message = "forge: reject out-of-bounds patch"
            detail = f"Patch rejected: {reason}"
        _save_state(state_path, state)
        devlog.append(devlog_path, status, task.text, detail)
        return 0 if _commit(repo_root, message, push) else 1

    tests_before = _safe_count_tests(repo_root)
    result = _judge(repo_root, patch)

    if result.ok:
        # A green suite is only meaningful if it is still the same suite. Patches may
        # write anywhere under tests/, so a task can be "completed" by replacing a
        # test file with a thinner one: ruff, import and pytest all pass, on less
        # coverage. Left unchecked that quietly dismantles the one guarantee this
        # repository makes about its own history.
        tests_after = _safe_count_tests(repo_root)
        if tests_before > 0 and 0 <= tests_after < tests_before:
            result = GuardrailResult(
                ok=False,
                log=(
                    f"{result.log}\n$ test-suite check\n"
                    f"Rejected: the suite shrank from {tests_before} to {tests_after} "
                    "collected tests. Implement the task without removing or replacing "
                    "existing tests.\n"
                ),
            )
        else:
            # A green suite that grew by nothing has proven nothing about new code.
            untested = honesty.untested_production_reason(
                patch.files, tests_before, tests_after
            )
            if untested:
                result = GuardrailResult(
                    ok=False,
                    log=f"{result.log}\n$ test-suite check\nRejected: {untested}\n",
                )

    if result.ok:
        _close_task_state(state, task.text)
        _save_state(state_path, state)
        _mark_done(backlog_path, task)
        devlog.append(
            devlog_path,
            "success",
            task.text,
            f"{patch.summary}\n\nGuardrail: ruff + import + pytest passed.",
        )
        return 0 if _commit(repo_root, f"forge: {patch.summary}", push) else 1

    _revert(repo_root)

    # Distinguish "the model wrote bad code" from "this checkout is broken". If the
    # guardrail still fails with the patch reverted, the failure predates the model:
    # a dependency released a new lint rule, a transitive break, a broken runner.
    # Blaming the task there would burn three attempts, skip it, and then do the same
    # to every remaining task — silently shredding the backlog while every run still
    # reports success. Record it instead and change nothing.
    baseline = _baseline(repo_root)
    if not baseline.ok:
        print("guardrail fails on a clean tree; environment is broken, not the patch")
        if not _outage_already_logged(repo_root, "environment"):
            devlog.append(
                devlog_path,
                "blocked",
                task.text,
                "The guardrail fails on a clean checkout, before any generated code is "
                "applied, so the build environment is broken rather than the patch. The "
                "task is left untouched and no attempt was counted.\n\n"
                f"{_tail(baseline.log)}",
            )
            published = _commit(
                repo_root, "forge: log blocked task (environment unavailable)", push
            )
            return 0 if published else 1
        return 0

    attempts += 1
    state[task.text] = attempts
    _remember_failure(state, task.text, result.log)

    if attempts >= args.max_attempts:
        _mark_done(backlog_path, task, f"skipped after {attempts} failed attempts")
        status, message = "skipped", "forge: skip task after repeated guardrail failures"
        _close_task_state(state, task.text)
    else:
        status, message = "failed", "forge: log failed attempt (code reverted)"

    _save_state(state_path, state)

    devlog.append(
        devlog_path,
        status,
        task.text,
        f"Guardrail failed on attempt {attempts}; code reverted.\n\n```\n{_tail(result.log)}\n```",
    )
    return 0 if _commit(repo_root, message, push) else 1


if __name__ == "__main__":
    raise SystemExit(main())
