from lib.handling.method_handlers import GET,POST
from lib.routning.radix import NONE, TREE_NODE, encoder, finalize, decoder

tree = bytearray(TREE_NODE.size)
tree_values, tree_methods, param_pairs = bytearray(), bytearray(), []
TREE_NODE.pack_into(tree, 0, 0, 0, NONE, NONE, -1, NONE, 0, 0)

for route, method, handler_id in (
    (b"/users/me", GET, 10),
    (b"/users/me/text/read", GET, 20),
    (b"/users/{id}/posts/good", GET, 30),
    (b"/users/{id}/posts/good",POST,30),
):
    new_route = b"/" + bytes([method]) + route
    print(new_route)
    encoder(new_route, tree, tree_values, tree_methods, handler_id, param_pairs)

finalize(tree, tree_values, param_pairs)

assert decoder(b"/" + bytes([GET]) + b"/users/me", GET, tree, tree_values, tree_methods)[0] == 10
assert decoder(b"/\x01/users/me/text/read", GET, tree, tree_values, tree_methods)[0] == 20
handler_id, params = decoder(b"/\x01/users/3/posts/good", GET, tree, tree_values, tree_methods)
assert handler_id == 30 and params == [(b"id", b"3")]
handler_id, params = decoder(b"/\x01/users/me/posts/good", GET, tree, tree_values, tree_methods)
assert handler_id == 30 and params == [(b"id", b"me")]
print(decoder(b"/" + bytes([POST]) + b"/users/me/posts/good", POST, tree, tree_values, tree_methods)[0])
assert decoder(b"/" + bytes([POST]) + b"/users/me/posts/good", POST, tree, tree_values, tree_methods)[0] == 30
#print(tree)


