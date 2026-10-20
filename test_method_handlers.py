from lib.handling.method_handlers import (
    GET, HEAD, POST, PUT, DELETE, CONNECT, OPTIONS, TRACE, PATCH,
    encode_method_handlers, decode_method_handler,
)


methods = (GET, HEAD, POST, PUT, DELETE, CONNECT, OPTIONS, TRACE, PATCH)
entries = tuple(zip(methods, (0, 11, 22, 33, 44, 55, 66, 77, 255)))
encoded = encode_method_handlers(entries)
assert encoded[0] == encoded[1] == 0b111111111
assert encoded[2] == bytearray((0, 11, 22, 33, 44, 55, 66, 77, 255))
for method, handler_id in entries:
    assert decode_method_handler(method, *encoded) == handler_id

# Five occupied positions, including both ends and handler ID zero.
entries = ((GET, 0), (POST, 20), (DELETE, 40), (OPTIONS, 60), (PATCH, 255))
encoded = encode_method_handlers(entries)
assert encoded[0] == encoded[1] == 0b101010101
assert len(encoded[2]) == 9
for method, handler_id in entries:
    assert decode_method_handler(method, *encoded) == handler_id
for method in (HEAD, PUT, CONNECT, TRACE):
    assert decode_method_handler(method, *encoded) is None

encoded = encode_method_handlers(((GET, 0), (GET, 255)))
assert encoded[0] == encoded[1] == GET
assert decode_method_handler(GET, *encoded) == 255

for entries in ((), ((0, 1),), ((GET | POST, 1),), ((1 << 9, 1),),
                ((GET, -1),), ((GET, 256),)):
    try:
        encode_method_handlers(entries)
    except ValueError:
        pass
    else:
        raise AssertionError(f"invalid registration accepted: {entries}")
