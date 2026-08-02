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
| `openai` | **recommended** — set `LLM_BASE_URL`, `MODEL_ID`, and `LLM_API_KEY` (Groq, Gemini's OpenAI-compatible endpoint, OpenRouter, a local Ollama, …) | free tiers exist |
| `github` | legacy; uses the workflow's `GITHUB_TOKEN` against GitHub Models | **being retired** |
| `mock` | deterministic, offline; used for tests and local verification | free |

> ⚠️ **GitHub Models is being retired.** As of this writing the inference
> endpoint returns `HTTP 410 github_models_retirement_brownout`, so the `github`
> provider is effectively unavailable. Use the `openai` provider with a free key
> instead — the loop is designed for exactly this swap.

A free key takes a minute to get. For example, with [Groq](https://console.groq.com):

```
LLM_PROVIDER=openai
LLM_BASE_URL=https://api.groq.com/openai/v1
MODEL_ID=llama-3.3-70b-versatile
LLM_API_KEY=<your free groq key>
```

Add those four as repository **Actions secrets** (Settings → Secrets and
variables → Actions) and the scheduled workflow picks them up automatically. If
no provider is reachable, a run does **not** break: it commits a "blocked" note
and retries next time.

## Honest caveats

This is an experiment, and it is described as one:

- **The default `github` provider is retired.** GitHub Models now returns 410, so
  out of the box every run logs "blocked" until you configure the `openai`
  provider with a free key (see above). This was verified live, not assumed.
- **Hosting the schedule for free needs a personal public repo.** GitHub Actions
  minutes are unmetered on public repositories. On **Enterprise Managed User
  (EMU)** accounts, public repositories and GitHub-hosted runners are often
  disabled by org policy — in which case the scheduled job cannot run on
  GitHub's infrastructure at all. Run it under a personal public account, or
  point a self-hosted runner at the repo, or drive `python -m builder.run` from a
  local `cron`/`launchd` job.
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
