from enum import Enum
from array import array
import lib.parsing.http_parse_automaton as p
import lib.parsing.http_headers_parser as hp
class Phase(Enum):
    HEADERS=1
    BODY = 2

class ParserResult(Enum):
    NEED_MORE_DATA=1
    BODY_PARSING_FINISHED=2
    HEADER_PARSING_FINISHED=3
    HEADER_PARSING_NEED_MORE_DATA=4
    
payload =  b"POST /api/data HTTP/1.1\r\n"
#RAW_STREAM = b"4\r\nWiki\r\n5\r\npedia\r\n0\r\n\r\n"
RAW_STREAM = b"POST /api/data HTTP/1.1\r\n\r\n4\r\nWiki\r\n5\r\npedia\r\n0\r\n\r\n"
def make_streaming_request_parser():
      input_buffer = bytearray()
      input_offset = 0
      body_parser_state = p.State.EXPECT_CHUNK_SIZE
      body_signal = p.NetworkInput.CHUNK_DATA_EMPTY
      body_current_value=0
      arena = bytearray(32)
      arena_offset=0
      phase = Phase.HEADERS
      offset_table = array("i")
      header_parser_state=hp.HeaderState.METHOD
      next_offset_id=6

      def feed(input_fragment):
          input_buffer.extend(input_fragment)
          nonlocal input_offset
          nonlocal body_parser_state
          nonlocal body_signal
          nonlocal body_current_value
          nonlocal arena_offset
          nonlocal phase
          nonlocal next_offset_id
          nonlocal header_parser_state
          nonlocal offset_table
          if phase == Phase.HEADERS:

              input_offset, offset_table,header_parser_state, next_offset_id = hp.parse_req_header(input_fragment,input_offset, offset_table, header_parser_state, next_offset_id)
              if header_parser_state == hp.HeaderState.SUCCESS:
                  phase = Phase.BODY
                  print(f"Success")
#                  return ParserResult.HEADER_PARSING_FINISHED, None
              else:
                  print(header_parser_state)
                  return ParserResult.HEADER_PARSING_NEED_MORE_DATA, None

          if phase == Phase.BODY:

              body_parser_state, body_signal, input_offset, body_current_value, arena_offset= p.run_engine(
                  body_parser_state,body_signal, body_current_value, input_buffer, input_offset, arena,arena_offset,trace_enabled=True
    )
              match body_parser_state:
                  case p.State.SUCCESS:
                      return ParserResult.BODY_PARSING_FINISHED, arena[:arena_offset]
                  case _ :
                      return ParserResult.NEED_MORE_DATA, arena
              

      return feed


feed = make_streaming_request_parser()

arena = None
for byte in RAW_STREAM:
    result,arena = feed(bytes([byte]))
    if result == ParserResult.HEADER_PARSING_FINISHED:
        print(result)
    else:
        print(f"Wrong: {result}")
        

print(arena)
