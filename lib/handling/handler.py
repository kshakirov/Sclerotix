from lib.parsing.http_headers_parser import Methods

def handle_get(req, arena=[]):
    print("recognized data  is {req}")
    response = b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"
    return  response

RESP_404_NOT_FOUND = memoryview(
    b"HTTP/1.1 404 Not Found\r\n"
    b"Content-Type: text/plain; charset=utf-8\r\n"
    b"Content-Length: 9\r\n"
    b"Connection: keep-alive\r\n"
    b"\r\n"
    b"Not Found"
)


def no_route(req,arena):
    return RESP_404_NOT_FOUND

ROUTES = {
    (Methods.GET, b"/index.html"): 
        handle_get
    
}

def hash_bytes(recognizing_data):
    return bytes(memoryview(recognizing_data['url']['buffer'][0:recognizing_data['url']['length']]))

    

def resolve_handler(url, method):
    found_url = ROUTES.get((method, url), no_route)
    return found_url
