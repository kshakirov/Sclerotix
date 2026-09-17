from lib.parsing.factory  import make_streaming_request_parser, ParserResult

payload =  b"POST /api/data HTTP/1.1\r\n"
#RAW_STREAM = b"4\r\nWiki\r\n5\r\npedia\r\n0\r\n\r\n"
RAW_STREAM = b"POST /api/data HTTP/1.1\r\ntransfer-encoding: chunked\r\n\r\n4\r\nWiki\r\n5\r\npedia\r\n0\r\n\r\n"

RAW_STREAM_CONST = (
      b"POST /api/data HTTP/1.1\r\n"
      b"content-length: 9\r\n"
      b"\r\n"
      b"Wikipedia"
  )




def test_parse(payload):
    expected_body =b"Wikipedia"
    collected_body = bytearray(len(expected_body))
    feed = make_streaming_request_parser()
    result = None
    arena_idx = 0
    for byte in payload:

        result,fragment = feed(bytes([byte]))
        if(fragment):
            for f in fragment:
                collected_body[arena_idx] = f
                arena_idx += 1

    print(expected_body)
    print(collected_body)
    assert(expected_body == collected_body)            
    assert(result == ParserResult.BODY_PARSING_FINISHED)

test_parse(RAW_STREAM_CONST)
test_parse(RAW_STREAM)
