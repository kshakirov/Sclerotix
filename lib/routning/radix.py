import struct
from lib.handling.method_handlers import encode_method_handlers, method_index



TREE_NODE = struct.Struct("<IHIIi")
FIRST_CHILD = struct.Struct("<I")
NEXT_SIBLING = struct.Struct("<I")
METHODS_OFFSET = struct.Struct("<i")
METHOD_RECORD = struct.Struct("<HH9s")
METHOD_MASKS = struct.Struct("<HH")
NONE = 0xFFFFFFFF
NOT_FOUND = -1
METHOD_NOT_ALLOWED = -2
SEG_LITERAL_TYPE=0
SEG_PARAM_TYPE=1
SEG_WILDCARD_TYPE=2


#def parse_parameter():

# here find must be implemented to make it without allocations and cycles
def read_segment(seq,i):
    length = len(seq)
    if seq[i] == 123:
        p_end = seq.find(125, i + 1)
        seg_end =seq.find(47, i + 1)
        if p_end > -1 and seg_end > -1 and seg_end - p_end ==1:
            return seg_end, SEG_PARAM_TYPE
        elif seg_end == -1 and length - p_end == 1:
            return length, SEG_PARAM_TYPE
        else:
            raise "Syntax error" #TODOT the error specific 
    else:    
        while i < length :
            match seq[i]:
                case 47:
                    return i,SEG_LITERAL_TYPE
                case _:
                    i+=1
        return  i, SEG_LITERAL_TYPE



def create_node(segment, tree,tree_values, parent_offset, seg_type, param_pairs):
    segment_offset = len(tree_values)
    segment_length = len(segment)
    if seg_type == SEG_PARAM_TYPE:
        segment_length = segment_length | 0x4000

         
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
    if seg_type == SEG_PARAM_TYPE:
        param_pairs.append((self_offset, parent_offset))
            
    return self_offset    
        

def is_parameter_type(length):
    return length & 0x4000 == 0x4000


def search_segment(segment, tree,tree_values, offset, seg_type, decoder=False ):
    first_child = FIRST_CHILD.unpack_from(tree, offset + 6)[0]
    param_node = None
    mv_tree_values = memoryview(tree_values)
    if first_child != NONE:
        so,sl,_,ns,_ = (TREE_NODE.unpack_from(tree, first_child) )

        if seg_type == SEG_PARAM_TYPE:
            sl = sl & 0x3FFF

        if segment == mv_tree_values[so:(so + sl)]:
            return (True, first_child)

        if decoder and is_parameter_type(sl):
            param_node =  (first_child, (so,sl))

        if ns == NONE:
            if decoder and param_node:
                return (True, param_node)
            return (False, None)

        while (ns != NONE) :
            (so,sl,_,nns,_) = (TREE_NODE.unpack_from(tree, ns) )
            if is_parameter_type(sl):
                param_node= (ns,(so,sl))
            if seg_type == SEG_PARAM_TYPE:
                sl = sl & 0x3FFF 
            if segment == mv_tree_values[so:(so + sl)]:
                return (True, ns)
        
            ns = nns
        if decoder and param_node:
            return (True, param_node)
    return (False, None)
        
        
        


def create_clone_node(tree,tree_values, parent_offset, c_seg, c_seg_len,c_first_child_offset):
 
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
    param_data = []
    mv_segment = memoryview(route)
    while i < length:
        if route[i] == 47:
            start = i + 1
            end, seg_type = read_segment(route, start)
            i = end
            found, offset = search_segment(mv_segment[start:end], tree, tree_values, parent_offset, seg_type, True)
            if isinstance(offset, tuple):
                offset, (param_offset, param_length) = offset
                param_data.append((mv_segment, param_offset, param_length))
            if not found:
                return NOT_FOUND
            parent_offset = offset
        else:
            i += 1

    methods_offset = METHODS_OFFSET.unpack_from(tree, parent_offset + 14)[0]
    if methods_offset == -1:
        return NOT_FOUND
    methods_mask, indices_mask = METHOD_MASKS.unpack_from(tree_methods, methods_offset)
    if methods_mask != indices_mask:
        raise ValueError("method and occupied-position masks must match")
    if not methods_mask & method:
        return METHOD_NOT_ALLOWED
    return tree_methods[methods_offset + METHOD_MASKS.size + index]

def encoder(route, tree, tree_values, tree_methods, method, handler_id, param_pairs):
    methods_mask, indices_mask, handlers = encode_method_handlers(
        ((method, handler_id),)
    )
    length = len(route)
    parent_offset = 0
    i =0
    mv_segment = memoryview(route)
    while i  < length:
        match route[i]:
            case 47:
                start = i + 1
                end, seg_type = read_segment(route,i + 1)
                i = end 
                (found, offset) = search_segment(mv_segment[start:end],tree, tree_values, parent_offset, seg_type)
                if found:
                    parent_offset = offset
                    continue
                else:
                    parent_offset = create_node(mv_segment[start:end],tree,tree_values, parent_offset, seg_type, param_pairs)
                    
                
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
            
                    
  

    
def create_clone_node(tree,tree_values, parent_offset, c_seg, c_seg_len,c_first_child_offset):
 
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
