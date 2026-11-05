from lib.parsing.http_headers_parser import Methods
from lib.routning.radix import NONE, TREE_NODE, NOT_FOUND, encoder, decoder, finalize


# The parser still uses Enum; the tree uses one byte per method.
METHOD_PREFIXES = {
    Methods.GET: b"/\x00", Methods.HEAD: b"/\x01", Methods.POST: b"/\x02",
    Methods.PUT: b"/\x03", Methods.DELETE: b"/\x04", Methods.PATCH: b"/\x08",
}


def make_router(routes):
    tree = bytearray()
    tree_values = bytearray()
    handlers = []
    registrations = {}
    dirty = True
    response_not_found = memoryview(
        b"HTTP/1.1 404 Not Found\r\n"
        b"Content-Type: text/plain; charset=utf-8\r\n"
        b"Content-Length: 9\r\n"
        b"Connection: close\r\n\r\nNot Found"
    )

    def no_route(request_state, arena_fragment, finished, context):
        return response_not_found

    def resolve_handler(url, method):
        nonlocal tree, tree_values, dirty
        if dirty:
            tree = bytearray(TREE_NODE.size)
            tree_values, param_pairs = bytearray(), []
            TREE_NODE.pack_into(tree, 0, 0, 0, NONE, NONE, -1, NONE, 0, 0)
            for path, handler_id in registrations.items():
                encoder(path, tree, tree_values, handler_id, param_pairs)
            finalize(tree, tree_values, param_pairs)
            dirty = False
        prefix = METHOD_PREFIXES[method]
        handler_id, params = decoder(prefix + url, tree, tree_values)
        if handler_id == NOT_FOUND:
            return no_route, None
        return handlers[handler_id], params

    def add_route(method, url, handler):
        nonlocal dirty
        path = METHOD_PREFIXES[method] + url
        for handler_id, registered in enumerate(handlers):
            if registered is handler:
                break
        else:
            handler_id = len(handlers)
            handlers.append(handler)
        registrations[path] = handler_id
        dirty = True

    for (method, url), handler in routes.items():
        add_route(method, url, handler)

    return resolve_handler, add_route
