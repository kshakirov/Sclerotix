from lib.routning.radix import encoder, NONE, TREE_NODE,read_segment,search_segment, finalize,decoder
from lib.handling.handler import make_router


GET     = 1 << 0  # 00000001
HEAD    = 1 << 1  # 00000010
POST    = 1 << 2  # 00000100
PUT     = 1 << 3  # 00001000
DELETE  = 1 << 4  # 00010000
CONNECT = 1 << 5  # 00100000
OPTIONS = 1 << 6  # 01000000
TRACE   = 1 << 7  # 10000000
PATCH   = 1 << 8  # 100000000

route_cases = (
    (b"/users/me", GET, 10),
    (b"/users/me/text/read", GET, 20),
    (b"/users/{id}/posts/good", GET, 30),
)



tree = bytearray(TREE_NODE.size)
tree_values = bytearray()
param_pairs = []
tree_methods = bytearray()
TREE_NODE.pack_into(tree, 0, 0, 0, NONE, NONE, -1)


for route, method, handler_id in route_cases:
    encoder(route, tree, tree_values, tree_methods, method, handler_id, param_pairs)
    
finalize(tree, tree_values, param_pairs)
    


decoder(route_cases[0], GET,tree,tree_values, tree_methods)

    
make_router(routes)
