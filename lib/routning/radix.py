import struct


def encode_segment(seq,i):
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
                segment, i = encode_segment(route,i + 1)
                print(f"segment is {segment}, i is {i}")
            case _:
                i+= 1
                print("the rest")
            
                    
  

route = b"/api/user/info/id"

tree = bytearray()

TREE_NODE = struct.Struct('<IHIHi')
segment_buffer = bytearray()
node_buffer = bytearray()
print(f"size is {TREE_NODE.size}")
encoder(route,0,segment_buffer, node_buffer)

    
