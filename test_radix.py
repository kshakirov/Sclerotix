from lib.routning.radix import NONE, TREE_NODE, encoder, SEG_PARAM_TYPE,FIRST_CHILD,NEXT_SIBLING
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

def create_clone_node(tree,tree_values, parent_offset, c_seg, c_seg_len,c_first_child_offset):
    # if seg_type == SEG_PARAM_TYPE:
    #     segment_length = segment_length | 0x4000
    #somewhere to bind m
    
         
#    tree_values.extend(segment)
    segment_offset = len(tree)
    tree.extend(bytearray(TREE_NODE.size))
    TREE_NODE.pack_into(tree, segment_offset,c_seg,c_seg_len,c_first_child_offset,NONE,-1)
    return segment_offset



def finalize(tree, tree_values, param_pairs):
    for (param_node_offset,parent_node_offset) in param_pairs:
        siblings = []
        _, _, first_child, _, _ = TREE_NODE.unpack_from(tree, parent_node_offset)
        _, _, param_node_first_child_offset, _, _ = TREE_NODE.unpack_from(tree, param_node_offset)
        c_seg, c_seg_len, c_first_child_offset = False,False,False
        if param_node_first_child_offset < 0xFFFFFFFF:
            c_seg, c_seg_len, c_first_child_offset, _, _ = TREE_NODE.unpack_from(tree, param_node_first_child_offset)
        sibling = first_child
        tree_length = len(tree)
        while  sibling:
            _, _,has_child, next_sibling, methods_offset = TREE_NODE.unpack_from(tree, sibling)
            print(f"current sibling {sibling}, next sibling {next_sibling}")
            if sibling != param_node_offset:
                siblings.append(sibling)
            if next_sibling and next_sibling < tree_length: 
                sibling = next_sibling
            else:
                sibling = None
                
        print(siblings)
        #next create a half copy  of one of siblings
        for s in siblings:
            print("prepareing to create a real child a copy of the parametrized one")
            #somewhere to bind parent to parameter?
            if c_seg:
                clone_node_offset = create_clone_node(tree,tree_values, param_node_offset,c_seg,c_seg_len,c_first_child_offset)
                old_first_child = FIRST_CHILD.unpack_from(tree, s + 6)
                FIRST_CHILD.pack_into(tree, s + 6, clone_node_offset)
                NEXT_SIBLING.pack_into(tree, clone_node_offset + 10, old_first_child[0])
                

pp = finalize(tree, tree_values, param_pairs)

    
assert len(tree) == TREE_NODE.size * 9
