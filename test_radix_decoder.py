from lib.handling.method_handlers import GET, POST, PUT, PATCH
from lib.routning.radix import (
    NONE, TREE_NODE, NOT_FOUND, METHOD_NOT_ALLOWED, encoder, decoder,
)


tree = bytearray(TREE_NODE.size)
tree_values = bytearray()
tree_methods = bytearray()
TREE_NODE.pack_into(tree, 0, 0, 0, NONE, NONE, -1)

registrations = (
    (b"/api/user", GET, 0),
    (b"/api/user", POST, 255),
    (b"/api/product", PUT, 17),
    (b"/api/order", PATCH, 42),
    (b"/api/user/info", GET, 7),
)
for route, method, handler_id in registrations:
    encoder(route, tree, tree_values, tree_methods, method, handler_id)

before = (bytes(tree), bytes(tree_values), bytes(tree_methods))
for route, method, handler_id in registrations:
    assert decoder(route, method, tree, tree_values, tree_methods) == handler_id

for route in (b"/missing", b"/api", b"/api/unknown", b"/api/user/missing"):
    assert decoder(route, GET, tree, tree_values, tree_methods) == NOT_FOUND

assert decoder(b"/api/user", PUT, tree, tree_values, tree_methods) == METHOD_NOT_ALLOWED
assert decoder(b"/api/order", GET, tree, tree_values, tree_methods) == METHOD_NOT_ALLOWED
assert (bytes(tree), bytes(tree_values), bytes(tree_methods)) == before

encoder(b"/api/user", tree, tree_values, tree_methods, GET, 99)
assert decoder(b"/api/user", GET, tree, tree_values, tree_methods) == 99
assert decoder(b"/api/user", POST, tree, tree_values, tree_methods) == 255
