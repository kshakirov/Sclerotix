"""Small scenarios; known Finalize limitations remain visible as failures."""
from lib.handling.handler import make_router
from lib.parsing.http_headers_parser import Methods

GET, POST = Methods.GET, Methods.POST


def a(*args): pass
def b(*args): pass


cases = (
    ("registration order", (
        (GET, b"/users/me", a),
        (GET, b"/users/{id}/posts/good", b),
    ), b"/users/me/posts/good", GET, b, [(b"id", b"me")]),
    ("nested parameters", (
        (GET, b"/users/{id}/posts/{post}", a),
    ), b"/users/3/posts/7", GET, a, [(b"id", b"3"), (b"post", b"7")]),
    ("clone and nested parameter", (
        (GET, b"/users/me", a),
        (GET, b"/users/{id}/posts/{post}", b),
    ), b"/users/me/posts/7", GET, b, [(b"id", b"me"), (b"post", b"7")]),
    ("method-specific priority", (
        (GET, b"/users/me/posts/good", a),
        (POST, b"/users/{id}/posts/good", b),
    ), b"/users/me/posts/good", GET, a, []),
    ("method-specific fallback", (
        (GET, b"/users/me/posts/good", a),
        (POST, b"/users/{id}/posts/good", b),
    ), b"/users/me/posts/good", POST, b, [(b"id", b"me")]),
)

failures = []
for name, registrations, url, method, expected, expected_params in cases:
    for ordered in (registrations, registrations[::-1]):
        resolve, _ = make_router({(m, path): handler for m, path, handler in ordered})
        handler, params = resolve(url, method)
        if handler is not expected or params != expected_params:
            failures.append((name, ordered == registrations, handler.__name__, params))
for failure in failures:
    print("FAIL:", failure)
assert not failures, f"{len(failures)} parameter routing checks failed"
