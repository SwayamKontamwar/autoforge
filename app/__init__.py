"""URL-shortener API — a real product built incrementally by the autoforge bot.

The seed implements health, create, and redirect. Every later feature is added
one backlog item at a time by ``builder/run.py``, guarded by lint + tests.
"""

# ----------------------------------------------------------------------
# Compatibility shim for test suites that still use the ``allow_redirects``
# argument with FastAPI's TestClient (which forwards to httpx).  The
# httpx client expects ``follow_redirects`` instead.  By monkey‑patching the
# ``get`` (and ``post``/``put``/``delete`` for completeness) methods we
# transparently map ``allow_redirects`` to ``follow_redirects`` so existing
# tests continue to work without modification.
# ----------------------------------------------------------------------
try:
    from fastapi.testclient import TestClient as _FastAPITestClient
except Exception:  # pragma: no cover
    _FastAPITestClient = None

if _FastAPITestClient is not None:
    _original_get = _FastAPITestClient.get
    _original_post = _FastAPITestClient.post
    _original_put = _FastAPITestClient.put
    _original_delete = _FastAPITestClient.delete

    def _patched_method(original):
        def wrapper(self, url, *args, allow_redirects=None, **kwargs):
            if allow_redirects is not None:
                # httpx uses ``follow_redirects``; map the legacy name.
                kwargs["follow_redirects"] = allow_redirects
            return original(self, url, *args, **kwargs)

        return wrapper

    _FastAPITestClient.get = _patched_method(_original_get)
    _FastAPITestClient.post = _patched_method(_original_post)
    _FastAPITestClient.put = _patched_method(_original_put)
    _FastAPITestClient.delete = _patched_method(_original_delete)
