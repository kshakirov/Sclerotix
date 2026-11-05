import struct
from lib.handling.method_handlers import encode_method_handlers, method_index



# Eight 32-bit fields, little-endian; all links are byte offsets.
TREE_NODE = struct.Struct("<IIIIiIII")
FIRST_CHILD_OFFSET = 8
NEXT_SIBLING_OFFSET = 12
METHODS_OFFSET_OFFSET = 16
PARAM_REF_OFFSET = 20
SEGMENT_TYPE_OFFSET = 24
FIRST_CHILD = struct.Struct("<I")
NEXT_SIBLING = struct.Struct("<I")
METHODS_OFFSET = struct.Struct("<i")
HANDLERS_RECORD = struct.Struct("<B")
METHOD_MASKS = struct.Struct("<HH")
NONE = 0xFFFFFFFF
NOT_FOUND = -1
METHOD_NOT_ALLOWED = -2
SEG_LITERAL_TYPE=0
SEG_PARAM_TYPE=1
SEG_WILDCARD_TYPE=2
SEG_CLONE_TYPE=3


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

         
    first_child= NONE
    next_sibling = NONE
    self_offset = len(tree)
    tree_values.extend(segment)
    tree.extend(bytearray(TREE_NODE.size))
    TREE_NODE.pack_into(tree, self_offset,segment_offset,segment_length,NONE,NONE,-1,NONE,seg_type,0)
    so, sl, first_child, ns, h_id, param_ref, node_type, reserved = (TREE_NODE.unpack_from(tree, parent_offset))
    if first_child == NONE:
        TREE_NODE.pack_into(tree, parent_offset,so,sl, self_offset,ns,h_id,param_ref,node_type,reserved)
    else:
        so,sl,fc,ns,hid,param_ref,node_type,reserved = (TREE_NODE.unpack_from(tree, first_child) )
        if ns == NONE:
            TREE_NODE.pack_into(tree, first_child,so,sl,fc,self_offset,hid,param_ref,node_type,reserved)
        while (ns != NONE) :
            (so,sl,fc,nns,hid,param_ref,node_type,reserved) = (TREE_NODE.unpack_from(tree, ns) )
            if nns == NONE:
                TREE_NODE.pack_into(tree, ns,so,sl,fc,self_offset,hid,param_ref,node_type,reserved)
                break
            ns = nns
    if seg_type == SEG_PARAM_TYPE:
        param_pairs.append((self_offset, parent_offset))
            
    return self_offset    
        

def is_parameter_type(seg_type):
    return seg_type == SEG_PARAM_TYPE

def is_clone_type(seg_type):
    return seg_type == SEG_CLONE_TYPE



def search_segment(segment, tree,tree_values, offset, seg_type, decoder=False ):
    first_child = FIRST_CHILD.unpack_from(tree, offset + FIRST_CHILD_OFFSET)[0]
    param_node = None
    mv_tree_values = memoryview(tree_values)
    if first_child != NONE:
        so,sl,_,ns,_,param_ref,node_type,_ = (TREE_NODE.unpack_from(tree, first_child) )
        


        if segment == mv_tree_values[so:(so + sl)] and not is_clone_type(node_type):
            return (True, first_child)

        if decoder and is_parameter_type(node_type):
            param_node =  (first_child, (so,sl))

        if decoder and is_clone_type(node_type):
            po,pl,_,pns,_,_,node_type,_ = (TREE_NODE.unpack_from(tree, offset) )
            param_ref_o,param_ref_len,_,_,_,_,_,_ = (TREE_NODE.unpack_from(tree, param_ref) )
            param_node = (first_child, (param_ref_o,param_ref_len),mv_tree_values[po:(po + pl)])
            

        if ns == NONE:
            if decoder and param_node:
                return (True, param_node)
            return (False, None)

        while (ns != NONE) :
            (so,sl,_,nns,_,_,node_type,_) = (TREE_NODE.unpack_from(tree, ns) )
            if is_parameter_type(node_type):
                param_node= (ns,(so,sl))
            if segment == mv_tree_values[so:(so + sl)]:
                return (True, ns)
        
            ns = nns
        if decoder and param_node:
            return (True, param_node)
    return (False, None)
        
        
        


        
         

    


def process_segment():
    """   """

    pass


def decoder(route, method, tree, tree_values, tree_methods):
    """Return (handler ID, parameter pairs), or (error code, None).

    Each parameter pair contains memoryviews of its name and URL value.

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
                if len(offset)==2:
                    offset, (param_offset, param_length) = offset
                    name = memoryview(tree_values)[param_offset + 1:param_offset + param_length - 1]
                    param_data.append((name, mv_segment[start:end]))
                elif len(offset)==3:
                    offset, (param_offset, param_length), parent = offset
                    name = memoryview(tree_values)[param_offset + 1:param_offset + param_length - 1]
                    param_data.append((name, parent))

            if not found:
                return NOT_FOUND, None
            parent_offset = offset
        else:
            i += 1
    print(f"Found {route}")        
    methods_offset = METHODS_OFFSET.unpack_from(tree, parent_offset + METHODS_OFFSET_OFFSET)[0]
    if methods_offset == -1:
        return NOT_FOUND,None
    (handler_id,) = HANDLERS_RECORD.unpack_from(tree_methods, methods_offset)
    print(f"handler is {handler_id}")
    return handler_id, param_data

def encoder(route, tree, tree_values, tree_methods, handler_id, param_pairs):


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

    so, sl, first_child, next_sibling, methods_offset, param_ref, node_type, reserved = TREE_NODE.unpack_from(
        tree, parent_offset
    )
    if methods_offset == -1:
        methods_offset = len(tree_methods)
        tree_methods.extend(HANDLERS_RECORD.pack(handler_id))
        TREE_NODE.pack_into(
            tree, parent_offset, so, sl, first_child, next_sibling, methods_offset,
            param_ref, node_type, reserved
        )
    else:
       
        tree_methods[methods_offset] = handler_id
            
                    
  

    
def create_clone_node(tree,tree_values, parent_offset, c_seg, c_seg_len,c_first_child_offset, param_ref):
 
    segment_offset = len(tree)
    tree.extend(bytearray(TREE_NODE.size))
    TREE_NODE.pack_into(tree, segment_offset,c_seg,c_seg_len,c_first_child_offset,NONE,-1,param_ref,SEG_CLONE_TYPE,0)
    return segment_offset


#parent node offset is users param node offset is {id}, new me is its brother
def finalize(tree, tree_values, param_pairs):
    for (param_node_offset,parent_node_offset) in param_pairs:
        siblings = []
        _, _, first_child, _, _, _, _, _ = TREE_NODE.unpack_from(tree, parent_node_offset)
        _, _, param_node_first_child_offset, _, _, _, _, _ = TREE_NODE.unpack_from(tree, param_node_offset)
        c_seg, c_seg_len, c_first_child_offset = False,False,False
        if param_node_first_child_offset < 0xFFFFFFFF:
            c_seg, c_seg_len, c_first_child_offset, _, _, _, c_seg_type, _ = TREE_NODE.unpack_from(tree, param_node_first_child_offset)
        sibling = first_child
        tree_length = len(tree)
        while  sibling:
            _, _,has_child, next_sibling, methods_offset, _, _, _ = TREE_NODE.unpack_from(tree, sibling)
           
            if sibling != param_node_offset:
                siblings.append(sibling)
            if next_sibling and next_sibling < tree_length: 
                sibling = next_sibling
            else:
                sibling = None
                
        #print(siblings)
        #next create a half copy  of one of siblings
        for s in siblings:

            #somewhere to bind parent to parameter?
            if c_seg:
                clone_node_offset = create_clone_node(tree,tree_values, param_node_offset,c_seg,c_seg_len,c_first_child_offset,param_node_offset)
                old_first_child = FIRST_CHILD.unpack_from(tree, s + FIRST_CHILD_OFFSET)
                FIRST_CHILD.pack_into(tree, s + FIRST_CHILD_OFFSET, clone_node_offset)
                NEXT_SIBLING.pack_into(tree, clone_node_offset + NEXT_SIBLING_OFFSET, old_first_child[0])
