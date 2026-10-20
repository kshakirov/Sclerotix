"""Direct correspondence between method bits and handler positions."""

GET = 1 << 0
HEAD = 1 << 1
POST = 1 << 2
PUT = 1 << 3
DELETE = 1 << 4
CONNECT = 1 << 5
OPTIONS = 1 << 6
TRACE = 1 << 7
PATCH = 1 << 8

METHOD_COUNT = 9


def method_index(method):
    """Return the position of one supported method bit."""
    if not isinstance(method, int) or not 0 < method < (1 << METHOD_COUNT):
        raise ValueError("method must be one of the nine method bits")
    if method & (method - 1):
        raise ValueError("method must contain exactly one set bit")
    return method.bit_length() - 1


def encode_method_handlers(entries):
    """Encode (method bit, handler ID) pairs; later entries replace earlier ones.

    Return method mask, occupied-position mask and nine handler bytes.
    Unoccupied bytes have no meaning; handler ID zero is valid.
    """
    methods_mask = 0
    indices_mask = 0
    handlers = bytearray(METHOD_COUNT)
    for method, handler_id in entries:
        index = method_index(method)
        if not isinstance(handler_id, int) or not 0 <= handler_id <= 255:
            raise ValueError("handler ID must be an integer from 0 to 255")
        methods_mask |= method
        indices_mask |= 1 << index
        handlers[index] = handler_id
    if not methods_mask:
        raise ValueError("at least one handler is required")
    return methods_mask, indices_mask, handlers


def decode_method_handler(method, methods_mask, indices_mask, handlers):
    """Return a handler ID or None when the method has no handler."""
    index = method_index(method)
    if methods_mask != indices_mask:
        raise ValueError("method and occupied-position masks must match")
    if len(handlers) != METHOD_COUNT:
        raise ValueError("exactly nine handler positions are required")
    if methods_mask & method:
        return handlers[index]
    return None
