# Development log

A dated, append-only record of every autoforge run. Successful runs describe the
feature that shipped; failed runs record that the code was reverted and why. The
log is written by the bot, not by hand.

## seed — human-authored starting point

The repository begins with a minimal but real FastAPI URL-shortener: a health
check, link creation, redirect, and a not-found path, all covered by tests. This
seed gives the model a concrete style to imitate. Everything below this line is
written by the autoforge builder.

## 2026-08-02T08:28Z — blocked: Reject invalid URLs on POST /links: require an http or https scheme and a host, returning 422 otherwise, with a test for a bad URL.

Model provider 'github' was unavailable: provider HTTP 410: {"error":{"code":"github_models_retirement_brownout","message":"GitHub Models is temporarily unavailable as part of a scheduled retirement brownout."}}
. No code changed; will retry next run.
