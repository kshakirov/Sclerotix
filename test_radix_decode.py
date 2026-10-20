from lib.routning.radix import encoder, NONE, TREE_NODE,read_segment,search_segment
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

routes = (
    b"/api/user",
    b"/api/product",
    b"/api/order",
    b"/api/user/info",
    b"/api/user/settings",
)

tree = bytearray(TREE_NODE.size)
tree_values = bytearray()
TREE_NODE.pack_into(tree, 0, 0, 0, NONE, NONE, -1)

for route in routes:
    encoder(route, tree, tree_values)

def decoder(route,tree,tree_values):
    length = len(route)
    parent_offset = 0
    i =0
    while i  < length:
        match route[i]:
            case 47:

                segment, i = read_segment(route,i + 1)

                (found, offset) = search_segment(segment,tree, tree_values, parent_offset)
                if found:
                    print("found")
                    parent_offset = offset
                else:
                    print("not found")
                    
                
            case _:
                i+= 1
            

    
    print(route)

decoder(routes[0],tree,tree_values)

    
make_router(routes)
