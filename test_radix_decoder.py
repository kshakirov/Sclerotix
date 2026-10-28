from lib.handling.method_handlers import GET
from lib.routning.radix import NONE, TREE_NODE, encoder, finalize, decoder

tree = bytearray(TREE_NODE.size)
tree_values, tree_methods, param_pairs = bytearray(), bytearray(), []
TREE_NODE.pack_into(tree, 0, 0, 0, NONE, NONE, -1)

for route, handler_id in (
    (b"/users/me", 10),
    (b"/users/me/text/read", 20),
    (b"/users/{id}/posts/good", 30),
):
    encoder(route, tree, tree_values, tree_methods, GET, handler_id, param_pairs)

finalize(tree, tree_values, param_pairs)
assert decoder(b"/users/me/posts/good", GET, tree, tree_values, tree_methods) == 30
assert decoder(b"/users/3/posts/good", GET, tree, tree_values, tree_methods) == 30
