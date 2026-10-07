from lib.parsing.http_headers_parser import Methods
from run_server_epoll import run_event_loop


RESPONSE_OK = memoryview(
    b"HTTP/1.1 200 OK\r\n"
    b"Content-Length: 0\r\n"
    b"Connection: close\r\n"
    b"\r\n"
)


def handle_request(request_state, arena_fragment, finished, context):
    if arena_fragment:
        context["body_bytes"] = context.get("body_bytes", 0) + len(arena_fragment)
    if finished:
        return RESPONSE_OK


ROUTES = {
    (Methods.GET, b"/index.html"): handle_request,
    (Methods.POST, b"/index.html"): handle_request,
    (Methods.PUT, b"/index.html"): handle_request,
}


if __name__ == "__main__":
    run_event_loop(host="127.0.0.1", port=8080, routes=ROUTES)
