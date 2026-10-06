import lib.handling.handler as h
import lib.parsing.http_headers_parser as hp
OFFSET_BASIS = 14695981039346656037
FNV_PRIME    = 1099511628211
MASK_64      = 2**64 - 1

print("hello, bro")

def sx_hash(hash, b):
    hash = hash ^ b
    return  (hash * FNV_PRIME) & MASK_64
    


def sx_hash_array(offset,bts):
    hash = offset
    for b in bts:
        hash = hash ^ b
        return (hash * FNV_PRIME) & MASK_64
    

print(sx_hash_array(OFFSET_BASIS, b"abcdefgh"))

def hash_routes(routes, offset):
    for k,v in routes:
        hash = sx_hash(offset, k.value)
        hash=sx_hash(hash, 0)
        return  sx_hash_array(hash, v)
        

handler_1 = lambda x : x 
handler_2 = lambda x : x + 1
routes= {(hp.Methods.POST, b"/product/view") : handler_1, (hp.Methods.GET, b"/index.html"): handler_2}

print(hash_routes(routes, OFFSET_BASIS))
 #  Для маршрута:

 #  обновить hash байтом метода
 #  обновить hash разделителем
 #  обновлять hash каждым байтом URL по мере разбора

 #  Методы у нас уже enum, поэтому берём его однозначный числовой код. Разделитель нужен, чтобы разные пары (method, URL) не образовали одну и ту же
 #  последовательность.
