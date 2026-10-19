import struct



TREE_NODE = struct.Struct("<IHIIi")
NONE = 0xFFFFFFFF

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


#jump 16 bytes depending on depth or leve
#if first time is easy but check if the node exists
#if exists do nothing save parent
#go down until you find non existing child it will be sibling of existing one you should find the last sibling then when you create this node must add reference to itself in that last sibling so you should go the chain of siblings

def search_segment(segment, tree,tree_values, offset ):
    segment_offset, segment_length, first_child, next_sibling, handler_id = (
        TREE_NODE.unpack_from(tree, offset))
    if first_child != NONE:
        (so,sl,_,ns,_) = (TREE_NODE.unpack_from(tree, first_child) )
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

def encoder(route, segment_offset,segment_buffer, node_buffer):
    length = len(route)
    depth = 0
    i =0
    while i  < length:
        match route[i]:
            case 47:
                print("got it")
                segment, i = read_segment(route,i + 1)
                print(f"segment is {segment}, i is {i}")
            case _:
                i+= 1
                print("the rest")
            
                    
  

route = b"/api/user/info/id"

#init tree with empty root
tree = bytearray(18)
tree_values_array = bytearray()



TREE_NODE.pack_into(tree, 0,0,0,NONE,NONE,-1)

print(TREE_NODE.size)
segment_buffer = bytearray()
node_buffer = bytearray()
print(f"size is {TREE_NODE.size}")
encoder(route,0,segment_buffer, node_buffer)

    
