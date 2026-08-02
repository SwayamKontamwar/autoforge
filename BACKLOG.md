# Backlog

autoforge works through this list top to bottom, one item per run. Each item is
small enough to implement and test in a single commit. Open items are `- [ ]`;
completed items become `- [x]`. Anyone can add, reorder, or rewrite items.

## API features

- [ ] Reject invalid URLs on POST /links: require an http or https scheme and a host, returning 422 otherwise, with a test for a bad URL.
- [ ] Add GET /links/{code}/info returning the code, target URL, and creation time as JSON without redirecting.
- [ ] Add DELETE /links/{code} that removes a link and returns 204, and make GET /{code} return 404 afterwards.
- [ ] Count redirects: track a hit counter per link and include it in the GET /links/{code}/info response.
- [ ] Add GET /links returning a JSON list of all links with their codes, targets, and hit counts.
- [ ] Add pagination to GET /links using limit and offset query parameters with sensible defaults and bounds.
- [ ] Support a custom alias on POST /links via an optional "code" field, returning 409 if the alias already exists.
- [ ] Validate custom aliases: allow only URL-safe characters and a length between 3 and 32, returning 422 otherwise.
- [ ] Add optional link expiry: accept an "expires_in_seconds" field and return 410 Gone when an expired link is visited.
- [ ] Add GET /stats returning totals: number of links, total redirects, and the most-visited code.
- [ ] Normalise created timestamps to timezone-aware UTC ISO 8601 strings everywhere they appear.
- [ ] Add a GET /healthz/details endpoint reporting uptime in seconds and the number of stored links.

## Persistence and structure

- [ ] Introduce a Storage protocol in app/storage.py so the in-memory store and future backends share one interface.
- [ ] Add a SQLite-backed store implementing the Storage protocol, selectable by an environment variable, defaulting to in-memory.
- [ ] Persist hit counts and expiry in the SQLite store so they survive a restart, with a test using a temp database file.

## Quality and hardening

- [ ] Add a global exception handler returning consistent JSON error bodies with a "detail" field.
- [ ] Add basic per-client rate limiting on POST /links using an in-memory token bucket, returning 429 when exceeded.
- [ ] Add request logging middleware that records method, path, and status without logging request bodies.
- [ ] Add a configurable maximum URL length and reject overly long targets with 422.
- [ ] Add an OpenAPI description and example to each endpoint so the generated docs read clearly.
- [ ] Add a GET / root endpoint returning the service name, version, and a link to /docs.
