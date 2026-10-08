# Temporary baseline before the streaming route hash experiment.
from lib.utils.hashing import hash_routes,OFFSET_BASIS,hash_route
def hash_bytes(recognizing_data):
    url = recognizing_data['url']
    return bytes(memoryview(url['buffer'])[:url['length']])


def make_router(routes):
    routes_by_key = hash_routes(routes, OFFSET_BASIS)
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

    def resolve_handler(hash, url, method):
        if hash in routes_by_key:
            #here we go whith the performance issue for for but
            bucket = routes_by_key[hash]
            for b in bucket:
                m,u,h = b
                if u == url and m == method:
                    return h

            return no_route
        else:
            return no_route

    def add_route(method, url, handler):
        key = hash_route(OFFSET_BASIS,method,url)
        if key in routes_by_key:
            routes_by_key[key].append((method,url, handler))
        else:
            routes_by_key[key] = [(method,url, handler)]

    return resolve_handler, add_route
