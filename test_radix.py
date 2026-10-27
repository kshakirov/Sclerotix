from lib.routning.radix import NONE, TREE_NODE, encoder, SEG_PARAM_TYPE
from lib.handling.method_handlers import GET


route_cases = (
    (b"/users/me", GET, 10),
    (b"/users/me/text/read", GET, 20),
    (b"/users/{id}/posts/good", GET, 30),
)

tree = bytearray(TREE_NODE.size)
tree_values = bytearray()
tree_methods = bytearray()
param_pairs = []
TREE_NODE.pack_into(tree, 0, 0, 0, NONE, NONE, -1)

for route, method, handler_id in route_cases:
    encoder(route, tree, tree_values, tree_methods, method, handler_id, param_pairs)

assert len(tree) == TREE_NODE.size * 8

print(param_pairs)


def finalize(tree, tree_values, param_pairs):
    for (param_node_offset,parent_node_offset) in param_pairs:
        siblings = []
        _, _, first_child, _, _ = TREE_NODE.unpack_from(tree, parent_node_offset)
        sibling = first_child
        tree_length = len(tree)
        while  sibling:
            _, _,has_child, next_sibling, methods_offset = TREE_NODE.unpack_from(tree, sibling)
            print(f"current sibling {sibling}, next sibling {next_sibling}")
            if sibling != param_node_offset and methods_offset >=0:
                siblings.append(sibling)
            if next_sibling and next_sibling < tree_length: 
                sibling = next_sibling
            else:
                sibling = None

        print(siblings)
        #next create a half copy  of one of siblings
    
                

pp = finalize(tree, tree_values, param_pairs)

    
