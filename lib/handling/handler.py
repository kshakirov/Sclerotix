from lib.parsing.http_headers_parser import Methods



#temporaly
def hash_bytes(recognizing_data):
    return bytes(memoryview(recognizing_data['url']['buffer'][0:recognizing_data['url']['length']]))


def make_router(routes={}):
    ROUTES = routes
    #for the time being later can be parametrize
    RESP_404_NOT_FOUND = memoryview(
    b"HTTP/1.1 404 Not Found\r\n"
    b"Content-Type: text/plain; charset=utf-8\r\n"
    b"Content-Length: 9\r\n"
    b"Connection: keep-alive\r\n"
    b"\r\n"
    b"Not Found"
    )
    def no_route(req,arena,finished):
        return RESP_404_NOT_FOUND
    def resolve_handler(url, method):
        found_url = ROUTES.get((method, url), no_route)
        return found_url
    def add_route(method, url, handler):
        ROUTES[(method,url)] = handler
    return resolve_handler, add_route
