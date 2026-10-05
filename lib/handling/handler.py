# Temporary baseline before the streaming route hash experiment.
def hash_bytes(recognizing_data):
    url = recognizing_data['url']
    return bytes(memoryview(url['buffer'])[:url['length']])


def make_router(routes):
    routes_by_key = routes
    response_not_found = memoryview(
        b"HTTP/1.1 404 Not Found\r\n"
        b"Content-Type: text/plain; charset=utf-8\r\n"
        b"Content-Length: 9\r\n"
        b"Connection: close\r\n"
        b"\r\n"
        b"Not Found"
    )

    def no_route(request_state, arena_fragment, finished, context):
        return response_not_found

    def resolve_handler(url, method):
        return routes_by_key.get((method, url), no_route)

    def add_route(method, url, handler):
        routes_by_key[(method, url)] = handler

    return resolve_handler, add_route
