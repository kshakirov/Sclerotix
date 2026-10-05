from lib.handling.handler import make_router
from lib.parsing.http_headers_parser import Methods

response_ok = b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"

def handle_get(request_state, arena_fragment, finished, context):
    context["calls"] = context.get("calls", 0) + 1
    if finished:
        return response_ok

resolve_handler, add_route = make_router({})
add_route(Methods.GET, b"/index.html", handle_get)

handler = resolve_handler(b"/index.html", Methods.GET)
assert handler is handle_get

context = {}
assert handler({}, memoryview(b"part"), False, context) is None
assert handler({}, memoryview(b"last"), True, context) == response_ok
assert context["calls"] == 2

no_route = resolve_handler(b"/index.html", Methods.POST)
assert no_route.__name__ == "no_route"
response = no_route({}, None, True, {})
assert bytes(response).startswith(b"HTTP/1.1 404 Not Found")
