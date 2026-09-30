from  lib.handling.handler import make_router
from lib.parsing.http_headers_parser import Methods

def handle_get(req, arena=[]):
    print(f"recognized data  is {req}")
    response = b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"
    return  response

resolve_handler, add_route = make_router()

add_route(Methods.GET,b"/index.html", handle_get)

handler =  resolve_handler(b"/index.html",Methods.GET)
assert handler.__name__ == "handle_get"
response = handler({'method': Methods.PUT, 'url': "/index.html"},[])


handler = resolve_handler(b"/index.html",Methods.POST)
assert handler.__name__ == "no_route"

response = handler({},[])

assert resolve_handler(b"/indexdd.html",Methods.DELETE)

