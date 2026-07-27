import random


from enum import Enum

class State(Enum):
    PARSE_HEADERS = 1
    EXPECT_CHUNK_SIZE= 2
    READ_CHUNK_DATA = 3
    SUCCESS= 4
    ERROR = 5
    EXPECT_CHUNK_CRLF=6

class NetworkInput(Enum):
    CHUNK_SIZE_GREATER_ZERO =1 
    CHUNK_SIZE_ZERO=2
    DATA_ARRIVED=3
    MALFORMED=4
    READING_FIXED_DATA=5
    HEADERS_PARSED_EMPTY=6
    HEADERS_PARSED_CONTENT_LENGTH=7
    HEADERS_PARSED_CHUNKED=8
    CHUNK_DATA_FLOW=10
    CHUNK_DATA_EMPTY=11
    CRLF_VALID=9
    


CONTENT_HEADER= "content-Length"
TRANSFER_ENCODING ="transfer-Encoding"





def convert_row_http_to_state_input(content_length_headers):
    print("convert")
    print(content_length_headers)
    
    match content_length_headers:
        case (True, None):
            return (TRANSFER_ENCODING, 0)
        case (True, c) if c > 0:
            return TRANSFER_ENCODING, c
        case (None, 0):
            return CONTENT_HEADER, 0
        case (None, c)  if c > 0:
            return CONTENT_HEADER, c
        case _ :
            return (NetworkInput.HEADERS_PARSED_EMPTY, None)


# as Hal suggested the name is
def transition(current_state, current_values, current_input):
    print(f" Transition{current_state, current_values, current_input}")
    match current_state:

        case State.PARSE_HEADERS if current_input == NetworkInput.HEADERS_PARSED_EMPTY:
            print("First case")
            return State.SUCCESS, None, None
        case State.PARSE_HEADERS if current_input == NetworkInput.HEADERS_PARSED_CONTENT_LENGTH:
            print("Second case")
            return (State.READ_CHUNK_DATA, current_values, NetworkInput.READING_FIXED_DATA)
        case State.PARSE_HEADERS if current_input == NetworkInput.HEADERS_PARSED_CHUNKED:
            print("Expecting chunk size state")
            size, i_nput = from_parse_chunk_to_expect_chunk_size()
            return State.EXPECT_CHUNK_SIZE, size, i_nput
        case State.EXPECT_CHUNK_SIZE if current_input == NetworkInput.CHUNK_SIZE_ZERO:
            print("Nothing to read chunk size is zero")
            return State.SUCCESS, None, None
        case State.EXPECT_CHUNK_SIZE if current_input == NetworkInput.MALFORMED:
            return State.ERROR,None,None
        case State.EXPECT_CHUNK_SIZE if current_input == NetworkInput.CHUNK_SIZE_GREATER_ZERO:
            print("from Expect Chunk Size to Chunk Size Greated Zero")
            return State.READ_CHUNK_DATA, current_values, NetworkInput.CHUNK_DATA_FLOW

        case State.READ_CHUNK_DATA if current_input == NetworkInput.READING_FIXED_DATA and current_values > 0 :
            print("Third Case")
            values = read_bytes_from_content(current_values)
            return State.READ_CHUNK_DATA, values, current_input
        case State.READ_CHUNK_DATA if current_input == NetworkInput.READING_FIXED_DATA and current_values ==0 :
            return State.SUCCESS,None,None
        case State.READ_CHUNK_DATA if current_input == NetworkInput.CHUNK_DATA_FLOW and current_values > 0 :
            return State.READ_CHUNK_DATA, current_values, current_input
        case State.READ_CHUNK_DATA if current_input == NetworkInput.CHUNK_DATA_FLOW and current_values == 0 :
            return State.EXPECT_CHUNK_CRLF, current_values, NetworkInput.CHUNK_DATA_EMPTY

        case State.READ_CHUNK_DATA if current_input == NetworkInput.CHUNK_DATA_EMPTY :
            return State.EXPECT_CHUNK_CRLF, None,None
        case State.EXPECT_CHUNK_CRLF if current_input == NetworkInput.CRLF_VALID:
            return State.EXPECT_CHUNK_SIZE,None,None
        case State.EXPECT_CHUNK_CRLF if current_input==NetworkInput.MALFORMED:
            return State.ERROR,None,None
        case _ :
            print("Failed to finde")
            return None,None,None
        
        
        
        
        
        

def parse_headers(http_row_data):
    #normalize header names
    return http_row_data

def prep_headers(http_row_data):
    state = State.PARSE_HEADERS
    headers = parse_headers(http_row_data) # прошлись по заголовкам собрали их
    #content_legnth = (TRANSFER_ENCODING in headers, headers.get(CONTENT_HEADER))
    content_legnth = 0
    network_input, current_value = convert_row_http_to_state_input(content_legnth)
    return (network_input, current_value)


def parse_http_content(state_tuple):
    state, value, i_nput = state_tuple
    counter = 0
    while  counter < 15:
          counter +=1 # времено
          #for i in range(0,10):
          newstate, new_value, network_input =transition(state, value, i_nput)
          print(f"newstate {newstate}, {new_value}")
          match newstate:
              case State.SUCCESS :
                  print("SUCCESS, finishing ...")
                  break #do someting 
              case State.ERROR:
                  #do something
                  print("ERROR")
                  break
             # case State.EXPECT_CHUNK_SIZE:
             #     pass
            # here we listen to socket for receiveng and reading headers
            # далее пакуему новое состояние с
              case State.EXPECT_CHUNK_CRLF:
                  pass
              case _:
                  print("Nothing found running again value is {}".format(new_value))
                  state,value, i_nput = newstate,new_value, network_input
                  
    return

def read_bytes_from_content(current_value):
    if(current_value > 0):
        #пока эмуллирует чтение затем добавим реальные
        # специально подробно расписываю
        new_value = current_value - 1
        return new_value
    else:
        return current_value

def from_parse_chunk_to_expect_chunk_size():
    #здесь мы читаем данные из сети и ищем  16 ричную строку
    if(True):
        return  0, NetworkInput.CHUNK_SIZE_ZERO
    else:
        return 0, NetworkInput.CHUNK_SIZE_GREATER_ZERO
