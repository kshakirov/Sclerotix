OFFSET_BASIS = 14695981039346656037
FNV_PRIME    = 1099511628211
MASK_64      = 2**64 - 1


def sx_hash(hash, b):
    hash = hash ^ b
    return  (hash * FNV_PRIME) & MASK_64
    


def sx_hash_array(offset,bts):
    hash = offset
    for b in bts:
        hash = hash ^ b
        hash =(hash * FNV_PRIME) & MASK_64
   #     print(hash)
    return hash
    


def hash_routes(routes, offset):
    new_routes = {}
    for k,v in routes:
        hash = sx_hash(offset, k.value)
        hash=sx_hash(hash, 0)
        hash = sx_hash_array(hash, v)
        value = routes[(k,v)]
        if hash in new_routes:
#            print(f"we already have a hash {hash}, a conflict, adding to bucket this value")
            new_routes[hash].append((k,v,value))
        else:
            new_routes[hash]= [(k,v,value)]
    return new_routes
        
def hash_route(offset, method, url):
    hash = sx_hash(offset, method.value)
    hash=sx_hash(hash, 0)
    return sx_hash_array(hash, url)
    

