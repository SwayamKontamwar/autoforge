from app.toolkit.webframework import Router


def test_static_and_parameterised_routes() -> None:
    router = Router()

    def static_handler() -> None: ...

    def param_handler() -> None: ...

    router.add_route("GET", "/foo", static_handler)
    router.add_route("GET", "/foo/{id}", param_handler)

    handler, params = router.match("GET", "/foo")
    assert handler is static_handler
    assert params == {}

    handler2, params2 = router.match("GET", "/foo/abc123")
    assert handler2 is param_handler
    assert params2 == {"id": "abc123"}


def test_precedence_static_over_param_when_added_later() -> None:
    router = Router()

    def param_handler() -> None: ...

    def static_handler() -> None: ...

    # Parameterised route added first
    router.add_route("GET", "/item/{name}", param_handler)
    # Static route added later should still win
    router.add_route("GET", "/item/special", static_handler)

    handler, params = router.match("GET", "/item/special")
    assert handler is static_handler
    assert params == {}


def test_method_mismatch_returns_none() -> None:
    router = Router()

    def handler() -> None: ...

    router.add_route("POST", "/submit", handler)

    handler_match, params = router.match("GET", "/submit")
    assert handler_match is None
    assert params == {}
