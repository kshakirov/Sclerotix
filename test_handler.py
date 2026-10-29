from lib.handling.handler import make_router
from lib.parsing.http_headers_parser import Methods

response_ok = b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"

def handle_get(request_state, arena_fragment, finished, context):
    context["calls"] = context.get("calls", 0) + 1
    if finished:
        return response_ok

resolve_handler, add_route = make_router({})
add_route(Methods.GET, b"/index.html", handle_get)

handler, params = resolve_handler(b"/index.html", Methods.GET)
assert handler is handle_get
assert params == []

context = {}
assert handler({}, memoryview(b"part"), False, context) is None
assert handler({}, memoryview(b"last"), True, context) == response_ok
assert context["calls"] == 2

no_route, params = resolve_handler(b"/index.html", Methods.POST)
assert params is None
assert no_route.__name__ == "method_not_allowed"
assert bytes(no_route({}, None, True, {})).startswith(b"HTTP/1.1 405 Method Not Allowed")

no_route, params = resolve_handler(b"/missing", Methods.GET)
assert params is None
assert no_route.__name__ == "no_route"
response = no_route({}, None, True, {})
assert bytes(response).startswith(b"HTTP/1.1 404 Not Found")

resolve_initial, _ = make_router({(Methods.GET, b"/index.html"): handle_get})
assert resolve_initial(memoryview(b"/index.html"), Methods.GET)[0] is handle_get

def handle_post(request_state, arena_fragment, finished, context):
    return response_ok

add_route(Methods.POST, b"/index.html", handle_post)
assert resolve_handler(b"/index.html", Methods.GET)[0] is handle_get
assert resolve_handler(b"/index.html", Methods.POST)[0] is handle_post
add_route(Methods.GET, b"/index.html", handle_post)
assert resolve_handler(b"/index.html", Methods.GET)[0] is handle_post

resolve_params, _ = make_router({(Methods.GET, b"/users/{id}/posts"): handle_get})
handler, params = resolve_params(b"/users/3/posts", Methods.GET)
assert handler is handle_get and params == [(b"id", b"3")]
