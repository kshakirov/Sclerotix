from  lib.handling.handler import resolve_handler
from lib.parsing.http_headers_parser import Methods

handler =  resolve_handler(b"/index.html",Methods.GET)
assert handler
response = handler({},[])
print(response)

handler = resolve_handler(b"/index.html",Methods.POST)
assert handler
response = handler({},[])
print(bytes(response))


assert resolve_handler(b"/indexdd.html",Methods.DELETE)

