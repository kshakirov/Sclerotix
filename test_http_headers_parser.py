from lib.parsing.http_headers_parser import parse_req_header, HeaderState, cmp_header_names,cmp_ascii_one_by_one, get_headers, is_transfer_encoding,get_content_length_if_content_length, ParserRequiredHeaders
from array import array
from math import floor,ceil

payload =  b"POST /api/data HTTP/1.1\r\n"
payload_cutA =  b"POST /api/dat"
payload_cutB =  b"a HTTP/1.1\r\n"
raw_get_request_wrong = b"POST /api/v1/status HTTP/1.1\r\nHost: localhost:8080\r\nUser-Agent: SclerotixClient/1.0\r\nTransfer-Encoding: chunkeddd\r\nAccept: */*\r\n\r\n4\r\nWiki\r\n5\r\npedia\r\n0\r\n\r\n"
raw_get_request = (
    b"POST /api/v1/status HTTP/1.1\r\n"
    b"Host: localhost:8080\r\n"
    b"User-Agent: SclerotixClient/1.0\r\n"
    b"transfer-encoding: chunked\r\n"
    b"Accept: */*\r\n"
    b"\r\n"
    b"4\r\nWiki\r\n5\r\npedia\r\n0\r\n\r\n"
)
RAW_STREAM = (
      b"POST /api/data HTTP/1.1\r\n"
      b"content-length: 123\r\n"
      b"\r\n"
      b"Wikipedia"
  )






def test_parse_header(payload):
      state =HeaderState.METHOD
      offset_table = array('i') # на время только
      next_offset_id =6
      input_offset = 0
      stream_recognizing_data = { 'headers': {'chunk_content_match':0,     'fixed_content_mattch':0, 'content_type': None, 'content_length': 0}}
      for b in payload:
            input_offset, offset_table,state, next_offset_id, stream_recognizing_data = parse_req_header([b],input_offset, offset_table,state, next_offset_id, stream_recognizing_data)
      return offset_table, stream_recognizing_data




# r,data = is_transfer_encoding(test_parse_header(raw_get_request_wrong),raw_get_request_wrong)
# assert(not r)

r,data = test_parse_header(raw_get_request)
assert(data['headers']['content_type'] == ParserRequiredHeaders.TRANSFER_ENCODING)
r,data = test_parse_header(RAW_STREAM)
print(data)
assert(data['headers']['content_type'] == ParserRequiredHeaders.CONTENT_LENGTH)
print(data)

