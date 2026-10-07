from lib.utils.hashing import hash_route, hash_routes,OFFSET_BASIS
from lib.parsing.http_headers_parser import Methods

handler_1 = lambda x : x 
handler_2 = lambda x : x + 1
routes= {(Methods.POST, b"/product/view") : handler_1, (Methods.GET, b"/index.html"): handler_2}
new_routes = hash_routes(routes, OFFSET_BASIS)
for method,url in routes:
    key = hash_route(OFFSET_BASIS, method, url)
    assert new_routes[key]
    bucket = new_routes[key]
    for b in bucket:
        m,u,handler = b
        if m == method and method == Methods.POST:
            assert handler == handler_1
        else:
            assert handler == handler_2
        
    
    

