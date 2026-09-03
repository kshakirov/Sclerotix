from lib.parsing.http_headers_parser import parse_req_header, HeaderState, cmp_header_names,cmp_ascii_one_by_one, get_headers, is_transfer_encoding
from array import array
from math import floor,ceil

payload =  b"POST /api/data HTTP/1.1\r\n"
payload_cutA =  b"POST /api/dat"
payload_cutB =  b"a HTTP/1.1\r\n"

state =HeaderState.METHOD
offset_table = array('i') # на время только
next_offset_id =6
input_offset = 0
raw_get_request = b"POST /api/v1/status HTTP/1.1\r\nHost: localhost:8080\r\nUser-Agent: SclerotixClient/1.0\r\nTransfer-Encoding: chunked\r\nAccept: */*\r\n\r\n4\r\nWiki\r\n5\r\npedia\r\n0\r\n\r\n"


raw_get_request = (
    b"POST /api/v1/status HTTP/1.1\r\n"
    b"Host: localhost:8080\r\n"
    b"User-Agent: SclerotixClient/1.0\r\n"
    b"Transfer-Encoding: chunked\r\n"
    b"Accept: */*\r\n"
    b"\r\n"
    b"4\r\nWiki\r\n5\r\npedia\r\n0\r\n\r\n"
)

RAW_STREAM = (
      b"POST /api/data HTTP/1.1\r\n"
      b"Content-Length: 9\r\n"
      b"\r\n"
      b"Wikipedia"
  )



for b in raw_get_request:
      input_offset, offset_table,state, next_offset_id = parse_req_header([b],input_offset, offset_table,state, next_offset_id)



# start,end = get_headers(offset_table, raw_get_request, b"transfer-encoding")
# print(start,end)

# start,end = get_headers(offset_table, raw_get_request, b"transfer-encoding")
# print(start,end)


# start,end = get_headers(offset_table, raw_get_request, b"content-length")
# print(start,end)

r = is_transfer_encoding(offset_table,raw_get_request)
print(r)
