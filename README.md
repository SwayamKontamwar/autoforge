# autoforge

[![daily build](https://github.com/SwayamKontamwar/autoforge/actions/workflows/daily-build.yml/badge.svg)](https://github.com/SwayamKontamwar/autoforge/actions/workflows/daily-build.yml)
[![python](https://img.shields.io/badge/python-3.11%2B-blue)](pyproject.toml)
[![license](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**A repository that writes itself.**

Several times a day a scheduled GitHub Action wakes up, reads the next task from
[`BACKLOG.md`](BACKLOG.md), asks a language model to implement it, and commits the
result — but only if the change passes lint, imports cleanly, and keeps the entire
test suite green. If it doesn't, the code is thrown away and the run writes an
honest note in [`DEVLOG.md`](DEVLOG.md) explaining what failed.

No human reviews the commits. The guarantee isn't supervision — it's that
**nothing reaches `main` unless it proved itself first.**

- 🔨 **[`BACKLOG.md`](BACKLOG.md)** — 2,000+ curated tasks, the roadmap it works through
- 📓 **[`DEVLOG.md`](DEVLOG.md)** — the journal it writes, successes and failures alike
- ✅ **[Actions](https://github.com/SwayamKontamwar/autoforge/actions)** — every build it has ever run

---

## What it's building

A working **URL shortener** in FastAPI, plus a standard-library-style utility
toolkit under `app/toolkit/`. It started as a 42-line seed with three endpoints.
Everything marked 🤖 was written, tested and committed by the bot — no human
touched it:

| | | |
| --- | --- | --- |
| `POST /links` | create a short link | 🌱 seed → 🤖 custom aliases, expiry, URL validation |
| `GET /{code}` | redirect to the target | 🌱 seed → 🤖 hit counting, `410` when expired |
| `GET /healthz` | liveness | 🌱 seed |
| `GET /links` | list every link with metadata | 🤖 |
| `GET /links/{code}/info` | inspect a single link | 🤖 |
| `DELETE /links/{code}` | remove a link | 🤖 |
| `GET /stats` | totals and most-visited | 🤖 |
| `GET /healthz/details` | uptime and link count | 🤖 |

Underneath, the bot also introduced a `Storage` protocol to decouple the handlers
from the in-memory backend, and normalised every timestamp to timezone-aware
ISO-8601.

Try it:

```bash
pip install -e ".[dev]" uvicorn
uvicorn app.main:app --reload
```

```console
$ curl -X POST localhost:8000/links -H 'content-type: application/json' \
       -d '{"url": "https://example.com/a/very/long/address"}'
{"code":"JlblZbu","url":"https://example.com/a/very/long/address"}

$ curl -i localhost:8000/JlblZbu
HTTP/1.1 307 Temporary Redirect
location: https://example.com/a/very/long/address
```

## How it works

```
cron ──► builder/run.py
        │
        ├─ pick the next unfinished task from BACKLOG.md
        ├─ send the model a relevance-ranked slice of the repo
        ├─ apply its patch  (app/ and tests/ only — nothing else is writable)
        │
        ├─ GUARDRAIL ── ruff ─► import ─► pytest ─► test-count
        │       │
        │       ├─ all pass ─► tick the task, log it, commit, push
        │       └─ any fail ─► revert the code, log why, commit the note
        │
        └─ exit cleanly, never leaving a broken tree
```

## Why every commit on `main` is green

The interesting problem isn't getting a model to write code. It's making sure
that when it writes something wrong — and it does — the repository doesn't
quietly absorb it. A red run is harmless. A **green run that is wrong** is the
one that matters, because nothing ever re-examines it.

So the loop is built around a few rules:

- **Nothing merges unproven.** Every patch must pass `ruff`, an import smoke
  check, and the full `pytest` suite. Anything else is reverted with
  `git checkout` + `git clean` and never reaches `main`.
- **The blast radius is fenced.** Generated patches may only write to `app/` and
  `tests/`. The builder, the workflow, and the backlog are out of bounds — a
  patch that reaches for them is rejected before it is applied.
- **The safety net can't be cut.** Since patches may write tests, the cheapest
  way to pass a hard task would be to delete the tests that make it hard.
  Collected tests are counted before and after, and a patch that shrinks the
  suite is rejected. Touching `app/` requires the count to go *up*.
- **The verdict can't be rigged.** Importing testing tools into `app/`, or
  rebinding attributes on the test client, is treated as out of bounds rather
  than as a clever solution.
- **A task is only ticked off by work that exists.** A patch with no files, or
  one that hands back existing files unchanged, is counted as a failed attempt
  instead of a silent success.
- **Failures teach.** The traceback is stored with the attempt and handed to the
  model next time, so a retry is a genuine second attempt rather than a rerun of
  the same mistake. After three failures a task steps aside so the loop keeps
  moving.
- **Nothing can wedge it.** Applying and judging a patch is crash-proof as a
  whole: any failure becomes an ordinary counted attempt with its error fed back,
  so no single bad patch can jam the same task forever.

## Built to run for years

[`BACKLOG.md`](BACKLOG.md) ships with **over 2,000 curated tasks** — generated by
[`tools/gen_backlog.py`](tools/gen_backlog.py) from a taxonomy of 81 real utility
categories (strings, math, dates, graphs, crypto helpers, statistics, geometry,
scheduling, parsing…), round-robined so early runs build breadth rather than
depth. Each one is small, self-contained, and independently testable.

But any finite list runs dry eventually, so **the backlog replenishes itself**.
When open tasks fall below a threshold, `builder/backlog_gen.py` mines the
toolkit the bot has *already built* and appends genuinely useful follow-up work —
more edge cases, input validation, worked examples. It needs no network and no
API key, and the pool grows as the toolkit grows.

The infrastructure is built for the same timescale. Hosted models get retired, so
when the configured one stops existing the builder asks the provider what it
actually serves, filters out models that can't write code, prefers a peer of the
retired one, and carries on. Storage is bounded — `DEVLOG.md` rotates into
`docs/devlog/` and finished tasks are archived out of `BACKLOG.md` — so no file
grows without limit.

## Free by construction

Not "cheap" — **zero**, and enforced in code rather than promised in a README.
GitHub's own accounting agrees: every run reports `billable_ubuntu_ms: 0`.

That holds because the repository is public (Actions minutes are free and
uncapped), the runner is `ubuntu-latest` (free), and inference runs on a free
tier with no payment method attached. All three could be undone by a one-word
edit, so `builder/cost.py` checks before spending and **refuses to run** if any
of them stops being free:

| if this changed | the run |
| --- | --- |
| repository turned private or internal | refuses — minutes are metered there |
| a larger, GPU, macOS or Windows runner | refuses — billed per minute even on public repos |
| the model endpoint isn't a known-free one | refuses — could bill per token |

The endpoint check is an **allow-list**, not a blocklist: anything not known to
be free is refused, because a blocklist is wrong the moment a new paid API
exists. And the guard can't be quietly unplugged — the test suite asserts the
workflow still passes its inputs in, and the guardrail runs that suite before
every commit.

## Run it yourself

```bash
git clone https://github.com/SwayamKontamwar/autoforge
cd autoforge
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

pytest                                        # 300+ tests, all green

python -m builder.run --provider mock --no-push   # drive the loop offline
```

The `mock` provider needs no network and no API key, so you can watch a full
cycle — pick, patch, guard, commit-or-revert — before configuring anything.

### Point it at a model

Add a single repository secret, `LLM_API_KEY`, and the scheduled workflow picks
it up. Base URL and model default to a free tier, and both can be overridden:

```bash
LLM_PROVIDER=openai
LLM_BASE_URL=https://api.groq.com/openai/v1   # or any OpenAI-compatible endpoint
MODEL_ID=openai/gpt-oss-120b
LLM_API_KEY=<your free key>
```

Anything speaking the OpenAI API works — Groq, Gemini's compatible endpoint,
OpenRouter, a local Ollama. If no provider is reachable the run doesn't break: it
records the outage and picks up where it left off next time.

## Layout

```
app/                 the service and toolkit being built
  main.py            the FastAPI URL shortener
  storage.py         the storage protocol and in-memory backend
  toolkit/           standard-library-style utilities
tests/               its test suite — every feature adds one

builder/             the engine that does the building
  run.py             orchestrator: pick → generate → guard → commit or revert
  llm.py             provider-agnostic client and patch parser
  guardrail.py       ruff + import + pytest
  backlog.py         read, advance and append BACKLOG.md
  backlog_gen.py     self-replenishing task generator
  cost.py            refuses to run anywhere that could be billed
  honesty.py         refuses patches that rig the verdict

tools/gen_backlog.py regenerates the curated backlog
.github/workflows/   the schedule that drives it all
BACKLOG.md           the roadmap        DEVLOG.md   the journal
```

## Scope

This is an experiment, and it's worth being straight about what it is. The
guardrail proves that code runs and does what its tests say — not that a senior
engineer would have designed it the same way; the backlog is written in small
steps to keep that trade-off reasonable. The model sees a relevance-ranked slice
of the repository rather than all of it, which is what keeps runs affordable
after years of daily commits. And scheduled runs on GitHub are best-effort:
slots drift, sometimes by hours. Five are scheduled a day because the project
only needs some of them to land — at one build a day, the backlog is still more
than five years of work.

## License

MIT — see [LICENSE](LICENSE).
