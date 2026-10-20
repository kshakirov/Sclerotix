from lib.handling import method_handlers as mh
from lib.parsing.http_headers_parser import Methods
from lib.routning.radix import (
    NONE, TREE_NODE, NOT_FOUND, METHOD_NOT_ALLOWED, encoder, decoder,
)


# Compatibility for callers still materializing the URL.
def hash_bytes(recognizing_data):
    url = recognizing_data['url']
    return bytes(memoryview(url['buffer'])[:url['length']])


def make_router(routes):
    tree = bytearray(TREE_NODE.size)
    tree_values = bytearray()
    tree_methods = bytearray()
    handlers = []
    TREE_NODE.pack_into(tree, 0, 0, 0, NONE, NONE, -1)
    method_bits = {
        Methods.GET: mh.GET, Methods.HEAD: mh.HEAD, Methods.POST: mh.POST,
        Methods.PUT: mh.PUT, Methods.DELETE: mh.DELETE, Methods.PATCH: mh.PATCH,
    }
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

    response_method_not_allowed = memoryview(
        b"HTTP/1.1 405 Method Not Allowed\r\n"
        b"Content-Length: 0\r\nConnection: close\r\n\r\n"
    )

    def method_not_allowed(request_state, arena_fragment, finished, context):
        return response_method_not_allowed

    def resolve_handler(url, method):
        method = method_bits.get(method, method)
        handler_id = decoder(url, method, tree, tree_values, tree_methods)
        if handler_id == NOT_FOUND:
            return no_route
        if handler_id == METHOD_NOT_ALLOWED:
            return method_not_allowed
        return handlers[handler_id]

    def add_route(method, url, handler):
        method = method_bits.get(method, method)
        mh.method_index(method)
        for handler_id, registered in enumerate(handlers):
            if registered is handler:
                break
        else:
            handler_id = len(handlers)
            if handler_id >= 256:
                raise ValueError("the handler registry supports at most 256 functions")
        encoder(url, tree, tree_values, tree_methods, method, handler_id)
        if handler_id == len(handlers):
            handlers.append(handler)

    for (method, url), handler in routes.items():
        add_route(method, url, handler)

    return resolve_handler, add_route
