from lib.parsing.factory  import make_streaming_request_parser, ParserResult

payload =  b"POST /api/data HTTP/1.1\r\n"
#RAW_STREAM = b"4\r\nWiki\r\n5\r\npedia\r\n0\r\n\r\n"
RAW_STREAM = b"POST /api/data HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\n4\r\nWiki\r\n5\r\npedia\r\n0\r\n\r\n"

RAW_STREAM_CONST = (
      b"POST /api/data HTTP/1.1\r\n"
      b"Content-Length: 9\r\n"
      b"\r\n"
      b"Wikipedia"
  )




def test_parse(payload):
    feed = make_streaming_request_parser()
    arena = None
    result = None
    for byte in payload:

        result,arena = feed(bytes([byte]))

    assert(result == ParserResult.BODY_PARSING_FINISHED)

test_parse(RAW_STREAM_CONST)
test_parse(RAW_STREAM)
