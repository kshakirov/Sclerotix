from enum import Enum
import lib.parsing.http_parse_automaton as p
class Phase(Enum):
    HEADERS=1
    BODY = 2

class ParserResult(Enum):
    NEED_MORE_DATA=1
    BODY_PARSING_FINISHED=2
    
payload =  b"POST /api/data HTTP/1.1\r\n"
RAW_STREAM = b"4\r\nWiki\r\n5\r\npedia\r\n0\r\n\r\n"

def make_streaming_request_parser():
      input_buffer = bytearray()
      input_offset = 0
      body_parser_state = p.State.EXPECT_CHUNK_SIZE
      body_input_offset =0
      body_signal = p.NetworkInput.CHUNK_DATA_EMPTY
      body_current_value=0
      arena = bytearray(32)
      arena_offset=0
      phase = Phase.HEADERS

      def feed(input_fragment):
          nonlocal input_offset
          nonlocal body_parser_state
          nonlocal body_signal
          nonlocal body_current_value
          nonlocal input_buffer
          nonlocal body_input_offset
          nonlocal arena_offset
          nonlocal phase
          print("I am feed")
          input_buffer.extend(input_fragment)
          body_parser_state, body_signal, body_input_offset, body_current_value, arena_offset= p.run_engine(
        body_parser_state,body_signal, body_current_value, input_buffer, body_input_offset, arena,arena_offset
    )
          match body_parser_state:
              case p.State.SUCCESS:
                  return ParserResult.BODY_PARSING_FINISHED, arena
              case _ :
                  return ParserResult.NEED_MORE_DATA, arena
              

      return feed


feed = make_streaming_request_parser()

arena = None
for byte in RAW_STREAM:
    result,arena = feed(bytes([byte]))
    print(result)

print(arena)
