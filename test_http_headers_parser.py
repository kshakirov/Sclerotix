from lib.parsing.http_headers_parser import parse_req_header, HeaderState
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



for b in raw_get_request:
      input_offset, offset_table,state, next_offset_id = parse_req_header([b],input_offset, offset_table,state, next_offset_id)

print(input_offset, offset_table,state, next_offset_id)

def get_headers(offset_table, payload, template):
      p = payload
      #maybe view instead of slice
      ot = offset_table[2:]
      for i in range(floor(len(ot) /4)):
            if(i >0):
                  r = i*4
                  print(p[ot[r]:ot[r + 1]] , p[ot[r + 2]:ot[r + 3]] )
                  if(template == p[ot[r]:ot[r + 1]]):
                        return p[ot[r + 2]:ot[r + 3]]
      return False

encoding = get_headers(offset_table, raw_get_request, b"Transfer-Encoding")
print(encoding)

content_length = get_headers(offset_table, raw_get_request, b"Content-Length")
print(content_length)
