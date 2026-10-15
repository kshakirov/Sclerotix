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
                

def encoder(route, segment_offset):
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
print(f"size is {TREE_NODE.size}")
encoder(route,0)

    
