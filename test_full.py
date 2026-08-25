from lib.parsing.http_headers_parser import parse_req_header
import lib.parsing.http_parse_automaton as p
payload =  b"POST /api/data HTTP/1.1\r\n"
RAW_STREAM = b"4\r\nWiki\r\n5\r\npedia\r\n0\r\n\r\n"
raw_get_request = (
    b"POST /api/v1/status HTTP/1.1\r\n"
    b"Host: localhost:8080\r\n"
    b"User-Agent: SclerotixClient/1.0\r\n"
    b"Accept: */*\r\n"
    b"\r\n"
    b"4\r\nWiki\r\n5\r\npedia\r\n0\r\n\r\n"
)
# now I give 2 more length to the last index of first automaton there must be a beginning of the body if it exists

def analyze_headers(req, table):
    # here we will check for content lenght or chunked
    state = p.State.EXPECT_CHUNK_SIZE
    in_put = p.NetworkInput.CHUNK_DATA_EMPTY 
    return state, in_put

def process_request(buffer, buffer_pointer, arena, arena_pointer,state, in_put, current_value):
    table, state = parse_req_header(buffer)
    buffer_pointer = table[len(table) -1] + 2
    print(raw_get_request[(table[len(table) -1] + 2): ])
    print("this is the body to process")
    state,in_put = analyze_headers(buffer, table)
    state, in_put, buffer_pointer, current_value, arena_pointer= p.run_engine(state, in_put, current_value, buffer, buffer_pointer, arena,arena_pointer)

    
    

#this file is a dispatcher prototype 

buffer = raw_get_request
buffer_pointer = 0
arena_pointer=0
arena = bytearray(64)
state = None
in_put = None
current_value = None # those None's will be saved in the coroutine

process_request(buffer, buffer_pointer, arena, arena_pointer, state,in_put,current_value)

