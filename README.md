# autoforge

**A public repository that builds itself.** Three times a day a scheduled GitHub
Actions job wakes up, reads the next item from [`BACKLOG.md`](BACKLOG.md), asks a
language model to implement it, and commits the result — but only if the change
passes lint and the full test suite. If it doesn't, the code is thrown away and
the run records an honest failure note instead. The product it is growing is a
real FastAPI URL-shortener API.

The point of the experiment is not the URL shortener. It is to see how far a
disciplined, test-guarded loop can carry an autonomous contributor while keeping
the repository honest: **every commit on `main` lints, imports, and passes its
tests, or it is a documentation-only note explaining why nothing shipped.**

## How it works

```
cron (3×/day) ──► builder/run.py
                     │
                     ├─ pick next "- [ ]" item from BACKLOG.md
                     ├─ ask a model for a whole-file patch (app/ and tests/ only)
                     ├─ apply it
                     ├─ GUARDRAIL: ruff check + import + pytest
                     │       ├─ pass ─► mark item done, log success, commit + push
                     │       └─ fail ─► revert code, log failure, commit the log
                     └─ exit 0 (never leaves a broken tree)
```

- **The guardrail is the whole promise.** `builder/guardrail.py` runs `ruff`, an
  import smoke check, and `pytest`. A patch that fails any of them is reverted
  with `git checkout` + `git clean` and never reaches `main`.
- **Blast radius is fenced.** Generated patches may only touch `app/` and
  `tests/`. Anything that tries to edit the builder, the workflow, or the backlog
  is rejected before it is applied.
- **Stalls are handled.** Attempts per task are tracked in `.forge/state.json`.
  After three failures a task is marked skipped so the loop keeps moving.
- **Failures are still commits.** A failed run commits a `DEVLOG.md` note, so the
  daily cadence and the audit trail continue even on a bad day.

## Running it yourself

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest                     # the seed suite is green

# Exercise the loop offline, without a network or API key, without committing:
python -m builder.run --provider mock --no-push
```

## Providers (and why it's free)

The builder is provider-agnostic. Pick one with `--provider` or `LLM_PROVIDER`:

| provider | how to configure | cost |
| --- | --- | --- |
| `github` | default; uses the workflow's `GITHUB_TOKEN` against GitHub Models | free |
| `openai` | set `LLM_BASE_URL`, `MODEL_ID`, and `LLM_API_KEY` (Groq, Gemini's OpenAI-compatible endpoint, OpenRouter, a local Ollama, …) | free tiers exist |
| `mock` | deterministic, offline; used for tests and local verification | free |

If GitHub Models is disabled for your account or org, the run does **not** break:
it commits a "blocked" note and retries next time. Switch to a free `openai`-
compatible key by adding repo secrets and the loop resumes.

## Honest caveats

This is an experiment, and it is described as one:

- **Free only for public repositories.** GitHub Actions minutes are unmetered on
  public repos; on a private repo the same three-runs-a-day schedule fits inside
  the monthly free allowance but is not unlimited.
- **Cron is best-effort.** GitHub may delay scheduled runs under load, so "three
  a day, four hours apart" is the intent, not a guarantee.
- **Sixty-day auto-disable.** GitHub disables scheduled workflows after 60 days
  with no repository activity; the daily commits themselves keep it alive.
- **The guardrail proves correctness, not taste.** Passing tests means the code
  runs and does what its tests say — not that a senior engineer would have
  designed it the same way. The backlog is written to keep each step small enough
  that this trade-off stays reasonable.
- **Model availability and rate limits vary.** Free inference tiers throttle; a
  throttled run simply logs that it was blocked and waits for the next slot.

## Layout

```
app/                 the URL-shortener being built
tests/               its test suite (every feature adds one)
builder/             the self-building engine
  run.py             orchestrator (pick → generate → guard → commit/revert)
  llm.py             provider-agnostic model client + strict JSON patch contract
  guardrail.py       ruff + import + pytest
  backlog.py         read/advance BACKLOG.md
  devlog.py          append dated notes to DEVLOG.md
.github/workflows/   the schedule that drives everything
BACKLOG.md           the roadmap the bot works through
DEVLOG.md            the journal the bot writes
```
