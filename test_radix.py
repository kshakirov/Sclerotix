from lib.routning.radix import NONE, TREE_NODE, encoder, SEG_PARAM_TYPE,FIRST_CHILD,NEXT_SIBLING, finalize
from lib.handling.method_handlers import GET,POST


route_cases = (
    (b"/users/me", GET, 10),
    (b"/users/me/text/read", GET, 20),
    (b"/users/{id}/posts/good", GET, 30),
    (b"/users/{id}/posts/good",POST,30),
)

tree = bytearray(TREE_NODE.size)
tree_values = bytearray()
tree_methods = bytearray()
param_pairs = []
TREE_NODE.pack_into(tree, 0, 0, 0, NONE, NONE, -1, NONE, 0, 0)

for route, method, handler_id in route_cases:
    new_route = b"/" + bytes([method]) + b"/" + route
    encoder(new_route, tree, tree_values, handler_id, param_pairs)

print(len(tree))
print(TREE_NODE.size)
assert len(tree) == TREE_NODE.size * 16

print(param_pairs)

                

pp = finalize(tree, tree_values, param_pairs)
print(len(tree))
print(TREE_NODE.size)
    
assert len(tree) == TREE_NODE.size * 17
