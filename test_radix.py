from lib.routning.radix import NONE, TREE_NODE, encoder, search_segment


route = b"/api/user/info/id"
expected_segments = (b"api", b"user", b"info", b"id")

tree = bytearray(TREE_NODE.size)
tree_values = bytearray()
TREE_NODE.pack_into(tree, 0, 0, 0, NONE, NONE, -1)

encoder(route, tree, tree_values)

assert tree_values == b"apiuserinfoid"
assert len(tree) == TREE_NODE.size * (len(expected_segments) + 1)

parent_offset = 0
for segment in expected_segments:
    found, node_offset = search_segment(
        segment, tree, tree_values, parent_offset
    )
    assert found
    assert node_offset == parent_offset + TREE_NODE.size

    segment_offset, segment_length, _, next_sibling, handler_id = (
        TREE_NODE.unpack_from(tree, node_offset)
    )
    assert tree_values[segment_offset:segment_offset + segment_length] == segment
    assert next_sibling == NONE
    assert handler_id == -1
    parent_offset = node_offset

tree_size = len(tree)
values_size = len(tree_values)
encoder(route, tree, tree_values)

assert len(tree) == tree_size
assert len(tree_values) == values_size
