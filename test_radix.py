from lib.routning.radix import NONE, TREE_NODE, encoder, search_segment, SEG_PARAM_TYPE, SEG_LITERAL_TYPE
from lib.routning.radix import METHOD_RECORD
from lib.handling.method_handlers import GET, POST, PATCH, decode_method_handler


route = b"/api/user/info/id"
expected_segments = (b"api", b"user", b"info", b"id")

tree = bytearray(TREE_NODE.size)
tree_values = bytearray()
tree_methods = bytearray()
TREE_NODE.pack_into(tree, 0, 0, 0, NONE, NONE, -1)

encoder(route, tree, tree_values, tree_methods, GET, 0)

assert tree_values == b"apiuserinfoid"
assert len(tree) == TREE_NODE.size * (len(expected_segments) + 1)

parent_offset = 0
for segment in expected_segments:
    found, node_offset = search_segment(
        segment, tree, tree_values, parent_offset,SEG_LITERAL_TYPE
    )
    assert found
    assert node_offset == parent_offset + TREE_NODE.size

    segment_offset, segment_length, _, next_sibling, handler_id = (
        TREE_NODE.unpack_from(tree, node_offset)
    )
    assert tree_values[segment_offset:segment_offset + segment_length] == segment
    assert next_sibling == NONE
    assert handler_id == (0 if segment == b"id" else -1)
    parent_offset = node_offset

tree_size = len(tree)
values_size = len(tree_values)
encoder(route, tree, tree_values, tree_methods, GET, 0)

assert len(tree) == tree_size
assert len(tree_values) == values_size
assert len(tree_methods) == METHOD_RECORD.size == 13

# Add another method, then replace GET without allocating a new record.
encoder(route, tree, tree_values, tree_methods, POST, 255)
encoder(route, tree, tree_values, tree_methods, GET, 7)
assert len(tree) == tree_size
assert len(tree_values) == values_size
assert len(tree_methods) == METHOD_RECORD.size
record = METHOD_RECORD.unpack_from(tree_methods, 0)
assert record[0] == record[1] == GET | POST
assert decode_method_handler(GET, *record) == 7
assert decode_method_handler(POST, *record) == 255
assert decode_method_handler(PATCH, *record) is None


routes = (
    b"/api/user",
    b"/api/product",
    b"/api/order",
    b"/api/user/info",
    b"/api/user/settings",
)

tree = bytearray(TREE_NODE.size)
tree_values = bytearray()
tree_methods = bytearray()
TREE_NODE.pack_into(tree, 0, 0, 0, NONE, NONE, -1)

for route in routes:
    encoder(route, tree, tree_values, tree_methods, GET, 0)

assert tree_values == b"apiuserproductorderinfosettings"
assert len(tree) == TREE_NODE.size * 7

found, api_offset = search_segment(b"api", tree, tree_values, 0,SEG_LITERAL_TYPE)
assert found

found, user_offset = search_segment(b"user", tree, tree_values, api_offset,SEG_LITERAL_TYPE)
assert found
found, product_offset = search_segment(b"product", tree, tree_values, api_offset,SEG_LITERAL_TYPE)
assert found
found, order_offset = search_segment(b"order", tree, tree_values, api_offset,SEG_LITERAL_TYPE)
assert found

_, _, _, user_sibling, _ = TREE_NODE.unpack_from(tree, user_offset)
_, _, _, product_sibling, _ = TREE_NODE.unpack_from(tree, product_offset)
_, _, _, order_sibling, _ = TREE_NODE.unpack_from(tree, order_offset)
assert user_sibling == product_offset
assert product_sibling == order_offset
assert order_sibling == NONE

found, info_offset = search_segment(b"info", tree, tree_values, user_offset,SEG_LITERAL_TYPE)
assert found
found, settings_offset = search_segment(
    b"settings", tree, tree_values, user_offset,SEG_LITERAL_TYPE
)
assert found

_, _, _, info_sibling, _ = TREE_NODE.unpack_from(tree, info_offset)
_, _, _, settings_sibling, _ = TREE_NODE.unpack_from(tree, settings_offset)
assert info_sibling == settings_offset
assert settings_sibling == NONE

tree_size = len(tree)
values_size = len(tree_values)
for route in routes:
    encoder(route, tree, tree_values, tree_methods, GET, 0)

assert len(tree) == tree_size
assert len(tree_values) == values_size
assert len(tree_methods) == len(routes) * METHOD_RECORD.size

# Registering descendants must preserve the parent's methods record.
for node_offset in (user_offset, product_offset, order_offset, info_offset, settings_offset):
    methods_offset = TREE_NODE.unpack_from(tree, node_offset)[4]
    assert methods_offset >= 0
    record = METHOD_RECORD.unpack_from(tree_methods, methods_offset)
    assert decode_method_handler(GET, *record) == 0
assert TREE_NODE.unpack_from(tree, api_offset)[4] == -1
