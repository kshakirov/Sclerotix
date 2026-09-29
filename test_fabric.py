from lib.parsing.factory  import make_streaming_request_parser, ParserResult
from lib.parsing.http_headers_parser import Methods

payload =  b"POST /api/data HTTP/1.1\r\n"
#RAW_STREAM = b"4\r\nWiki\r\n5\r\npedia\r\n0\r\n\r\n"
RAW_STREAM = b"POST /api/data HTTP/1.1\r\ntranSfer-encodINg: chunked\r\n\r\n4\r\nWiki\r\n5\r\npedia\r\n0\r\n\r\n"

RAW_STREAM_CONST = (
      b"POST /api/data HTTP/1.1\r\n"
      b"conTent-LenGth: 9\r\n"
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

        result,fragment, stream_recognizing_data = feed(bytes([byte]))
        if(fragment):
            for f in fragment:
                collected_body[arena_idx] = f
                arena_idx += 1
    assert memoryview(stream_recognizing_data['url']['buffer'])[0:stream_recognizing_data['url']['length']] == b'/api/data'
    assert stream_recognizing_data['methods']['guess'] == Methods.POST
    assert(expected_body == collected_body)            
    assert(result == ParserResult.BODY_PARSING_FINISHED)

    

test_parse(RAW_STREAM_CONST)
test_parse(RAW_STREAM)
