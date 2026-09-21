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
    ERROR=5
class ContentHeader(Enum):
    CONTENT_LENGTH=b"content-length"
    TRANSFER_ENCODING=b"transfer-encoding"

def make_streaming_request_parser():
      input_buffer = bytearray()
      header_stream_offset = 0
      body_parser_state = p.State.EXPECT_CHUNK_SIZE
      body_signal = p.NetworkInput.CHUNK_DATA_EMPTY
      body_current_value=0
      arena = bytearray(64 * 1024)
      arena_view= memoryview(arena)
      arena_offset=0
      phase = Phase.HEADERS
      offset_table = array("i")
      header_parser_state=hp.HeaderState.METHOD
      next_offset_id=6
      stream_recognizing_data = { 'headers': {'chunk_content_match':0, 'chunk_content_failed_prefix': False,    'fixed_content_mattch':0, 'fixed_content_failed_prefix': False, 'content_type': None, 'content_length': 0}}

      def feed(input_fragment):
          input_buffer = input_fragment
          body_fragment_offset = 0
          nonlocal header_stream_offset
          nonlocal body_parser_state
          nonlocal body_signal
          nonlocal body_current_value
          nonlocal arena_offset
          nonlocal phase
          nonlocal next_offset_id
          nonlocal header_parser_state
          nonlocal offset_table
          nonlocal arena
          nonlocal arena_view
          nonlocal stream_recognizing_data
          if phase == Phase.HEADERS:

              previous_header_stream_offset = header_stream_offset
              header_stream_offset, offset_table,header_parser_state, next_offset_id,stream_recognizing_data = hp.parse_req_header(input_fragment,header_stream_offset, offset_table, header_parser_state, next_offset_id,stream_recognizing_data)
              body_fragment_offset = header_stream_offset - previous_header_stream_offset
              found_header = None
              if header_parser_state == hp.HeaderState.SUCCESS:
#                  h_start, h_end = hp.get_headers(offset_table,input_buffer,ContentHeader.TRANSFER_ENCODING.value)# later change to constant
                  if stream_recognizing_data['headers']['content_type']== hp.ParserRequiredHeaders.TRANSFER_ENCODING:
                      body_parser_state = p.State.EXPECT_CHUNK_SIZE
                      phase = Phase.BODY
                      found_header = ContentHeader.TRANSFER_ENCODING

                      
                      #print(f"Success")
#                  h_start, h_end = hp.get_headers(offset_table,input_buffer,ContentHeader.CONTENT_LENGTH.value)# later change to constant
                  if stream_recognizing_data['headers']['content_type']== hp.ParserRequiredHeaders.CONTENT_LENGTH:
                      body_parser_state = p.State.PARSE_HEADERS# dont' remember which must be
                      body_signal = p.NetworkInput.HEADERS_PARSED_CONTENT_LENGTH
                      body_current_value =  stream_recognizing_data['headers']['content_length']# value from header must be parsed here
                      phase = Phase.BODY

                      if found_header == ContentHeader.TRANSFER_ENCODING:
                          return ParserResult.ERROR, None
                      else:
                          found_header= ContentHeader.CONTENT_LENGTH

                          #not needed any more   arena = bytearray(body_current_value)
                   # here comes checking for empty body later         

                  if not found_header:
                      #means no body interesting for us
                      return ParserResult.BODY_PARSING_FINISHED, None 
                  
              elif header_parser_state == hp.HeaderState.ERROR:
                  #do exit for later left
                  return ParserResult.ERROR, None
              
              else:
                  #print(header_parser_state)
                  return ParserResult.NEED_MORE_DATA, None

          if phase == Phase.BODY:
#              if len(input_buffer) > len(arena):
#                  arena.extend(bytearray(len(input_buffer) - len(arena))) #not very efficient for thet time being
              body_parser_state, body_signal, body_fragment_offset, body_current_value, arena_offset= p.run_engine(
                  body_parser_state,body_signal, body_current_value, input_buffer, body_fragment_offset, arena,arena_offset,trace_enabled=False
    )
              #print(f"FFFFF {body_parser_state}")
              match body_parser_state:
                  case p.State.SUCCESS:
                      fragment = arena_view[:arena_offset]
                      arena_offset = 0
                      return ParserResult.BODY_PARSING_FINISHED, fragment
                  case p.State.ERROR:
                      return ParserResult.ERROR, None
                  case _ :
                      fragment = arena_view[:arena_offset]
                      arena_offset = 0
                      return ParserResult.NEED_MORE_DATA, fragment
              

      return feed

