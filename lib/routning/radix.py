import struct
from lib.handling.method_handlers import encode_method_handlers, method_index



TREE_NODE = struct.Struct("<IHIIi")
METHOD_RECORD = struct.Struct("<HH9s")
METHOD_MASKS = struct.Struct("<HH")
NONE = 0xFFFFFFFF
NOT_FOUND = -1
METHOD_NOT_ALLOWED = -2

def read_segment(seq,i):
    segment = bytearray()

    length = len(seq)
    while i < length :
        match seq[i]:
            case 47:
                return segment, i
            case _:
                segment.append(seq[i])
                i+=1
    return segment, i



def create_node(segment, tree,tree_values, parent_offset):
    segment_offset = len(tree_values)
    segment_length = len(segment)
    first_child= NONE
    next_sibling = NONE
    self_offset = len(tree)
    tree_values.extend(segment)
    tree.extend(bytearray(TREE_NODE.size))
    TREE_NODE.pack_into(tree, self_offset,segment_offset,segment_length,NONE,NONE,-1)
    so, sl, first_child, ns, h_id = (TREE_NODE.unpack_from(tree, parent_offset))
    if first_child == NONE:
        TREE_NODE.pack_into(tree, parent_offset,so,sl, self_offset,ns,h_id)
    else:
        so,sl,fc,ns,hid = (TREE_NODE.unpack_from(tree, first_child) )
        if ns == NONE:
            TREE_NODE.pack_into(tree, first_child,so,sl,fc,self_offset,hid)
        while (ns != NONE) :
            (so,sl,fc,nns,hid) = (TREE_NODE.unpack_from(tree, ns) )
            if nns == NONE:
                TREE_NODE.pack_into(tree, ns,so,sl,fc,self_offset,hid)
                break
            ns = nns

    return self_offset    
        
        

def search_segment(segment, tree,tree_values, offset ):
    segment_offset, segment_length, first_child, next_sibling, handler_id = (
        TREE_NODE.unpack_from(tree, offset))
    if first_child != NONE:
        so,sl,_,ns,_ = (TREE_NODE.unpack_from(tree, first_child) )
        if segment == tree_values[so:(so + sl)]:
            return (True, first_child)
        if ns == NONE:
            return (False, None)

        while (ns != NONE) :
            (so,sl,_,nns,_) = (TREE_NODE.unpack_from(tree, ns) )
            if segment == tree_values[so:(so + sl)]:
                return (True, ns)
            ns = nns
    return (False, None)
        
        
        

        
         

    


def process_segment():
    """   """

    pass


def decoder(route, method, tree, tree_values, tree_methods):
    """Return handler ID (0..255), NOT_FOUND or METHOD_NOT_ALLOWED.

    Read-only traversal using the Builder's existing segment functions.
    """
    index = method_index(method)
    parent_offset = 0
    length = len(route)
    i = 0
    while i < length:
        if route[i] == 47:
            segment, i = read_segment(route, i + 1)
            found, offset = search_segment(segment, tree, tree_values, parent_offset)
            if not found:
                return NOT_FOUND
            parent_offset = offset
        else:
            i += 1

    methods_offset = TREE_NODE.unpack_from(tree, parent_offset)[4]
    if methods_offset == -1:
        return NOT_FOUND
    methods_mask, indices_mask = METHOD_MASKS.unpack_from(tree_methods, methods_offset)
    if methods_mask != indices_mask:
        raise ValueError("method and occupied-position masks must match")
    if not methods_mask & method:
        return METHOD_NOT_ALLOWED
    return tree_methods[methods_offset + METHOD_MASKS.size + index]

def encoder(route, tree, tree_values, tree_methods, method, handler_id):
    methods_mask, indices_mask, handlers = encode_method_handlers(
        ((method, handler_id),)
    )
    length = len(route)
    parent_offset = 0
    i =0
    while i  < length:
        match route[i]:
            case 47:

                segment, i = read_segment(route,i + 1)

                (found, offset) = search_segment(segment,tree, tree_values, parent_offset)
                if found:
                    parent_offset = offset
                    continue
                else:
                    parent_offset = create_node(segment,tree,tree_values, parent_offset)
                    
                
            case _:
                i+= 1

    so, sl, first_child, next_sibling, methods_offset = TREE_NODE.unpack_from(
        tree, parent_offset
    )
    if methods_offset == -1:
        methods_offset = len(tree_methods)
        tree_methods.extend(METHOD_RECORD.pack(methods_mask, indices_mask, handlers))
        TREE_NODE.pack_into(
            tree, parent_offset, so, sl, first_child, next_sibling, methods_offset
        )
    else:
        old_methods, old_indices = METHOD_MASKS.unpack_from(tree_methods, methods_offset)
        METHOD_MASKS.pack_into(
            tree_methods, methods_offset,
            old_methods | methods_mask, old_indices | indices_mask
        )
        tree_methods[methods_offset + METHOD_MASKS.size + method_index(method)] = handler_id
            
                    
  

    
