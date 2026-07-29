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




# as это чистый автомат  и функция который просто отмечает стадии чтения  ему на вход должны идти только состояние и входящий сигнал
def next_state(current_state, current_input, current_values):
    print(f"\tnext_state:  current tuple: {current_state, current_input, current_values}")
    match current_state:

        case State.PARSE_HEADERS if current_input == NetworkInput.HEADERS_PARSED_EMPTY:
            print("First case")
            return State.SUCCESS, None
        case State.PARSE_HEADERS if current_input == NetworkInput.HEADERS_PARSED_CONTENT_LENGTH:
            print("Second case")
            return (State.READ_CHUNK_DATA,  NetworkInput.READING_FIXED_DATA, current_values)
        case State.PARSE_HEADERS if current_input == NetworkInput.HEADERS_PARSED_CHUNKED:
            print("\tnext_state: transition to Expecting Chunk Size state")
            return State.EXPECT_CHUNK_SIZE, current_input, current_values
        case State.EXPECT_CHUNK_SIZE if current_input == NetworkInput.CHUNK_SIZE_ZERO:
            print("\tnext_state: Nothing to read chunk size is zero")
            return State.SUCCESS, None, None
        case State.EXPECT_CHUNK_SIZE if current_input == NetworkInput.MALFORMED:
            return State.ERROR,None,None
        case State.EXPECT_CHUNK_SIZE if current_input == NetworkInput.CHUNK_SIZE_GREATER_ZERO:
            print("from Expect Chunk Size to Chunk Size Greated Zero")
            return State.READ_CHUNK_DATA, current_values, NetworkInput.CHUNK_DATA_FLOW

        case State.READ_CHUNK_DATA if current_input == NetworkInput.READING_FIXED_DATA and current_values > 0 :
            print("Third Case")
            #values = read_bytes_from_content(current_values)
            return State.READ_CHUNK_DATA, current_input, current_values
        case State.READ_CHUNK_DATA if current_input == NetworkInput.READING_FIXED_DATA and current_values ==0 :
            print("0 bytes")
            return State.SUCCESS,None,None
        case State.READ_CHUNK_DATA if current_input == NetworkInput.CHUNK_DATA_FLOW and current_values > 0 :
            print("Reading chunks")
            value, in_put = read_chunk_data(current_values)
            return State.READ_CHUNK_DATA, value, in_put
        case State.READ_CHUNK_DATA if current_input == NetworkInput.CHUNK_DATA_FLOW and current_values == 0 :
            #            value, in_put = read_chunk_data(current_values)
            print("All data in chunk is read wating for CHUNK CRLF")
            in_put = expect_chunk_crlf()

            print("transition to Expect Chunk CRLF from 0 chunks left")
            return State.EXPECT_CHUNK_CRLF, current_values, NetworkInput.CHUNK_DATA_EMPTY

        case State.READ_CHUNK_DATA if current_input == NetworkInput.CHUNK_DATA_EMPTY :
            return State.EXPECT_CHUNK_CRLF, None,in_put
        case State.EXPECT_CHUNK_CRLF if current_input == NetworkInput.CRLF_VALID:
            return State.EXPECT_CHUNK_SIZE,None,None
        case State.EXPECT_CHUNK_CRLF if current_input==NetworkInput.MALFORMED:
            return State.ERROR,None,None
        case _ :
            print("Failed to find")
            return None,None,None
        
        
# это операционный автомат он на вход получает сигнал начальный или вообще он запускается без сигнала
#потоуму что он запускается только с сигналом чтение заголовков 
# но пока временно для тестирования у буду передавть сюда состояиния
def run_engine(state_tuple):
    #    state,  i_nput = State.PARSE_HEADERS, NetworkInput.HEADERS_PARSED_EMPTY
    state,  in_put, in_value = state_tuple
    counter = 0
    while  counter < 8:
        counter +=1 # времено
        #for i in range(0,10):

        print(f"run_engine: Entering Loop: state: {state}, in_put: {in_put}, in_value: {in_value}")
        match state:

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
            case State.EXPECT_CHUNK_SIZE :
                print(f"run_engine: state  is EXPECT_CHUNK_SIZE: in_put is {in_put} in_value is {in_value} ")
                in_put = read_chunk_size()
                
            case State.EXPECT_CHUNK_CRLF:
                pass
            case State.READ_CHUNK_DATA if in_put == NetworkInput.READING_FIXED_DATA:
                print("run_engine: Reading chunks of fixed length")
                bytes_left_to_read = read_chunk_fixed_length(in_value)
                state = State.READ_CHUNK_DATA
                in_put = NetworkInput.READING_FIXED_DATA
                in_value = bytes_left_to_read
                
                
                pass
            case _:
                print("run_engine: state is Default  Nothing Found,  running again state is {} network is {} looping  ...".format(state, in_put))
                

              #                  state,value, i_nput = newstate,new_value, network_input
        state,  in_put, in_value =next_state(state, in_put, in_value)

                  
    return


def read_chunk_fixed_length(current_value):
    print(f"\t\tread_chunk_fixed_length in_value is {current_value}")
    if(current_value > 0):
        #пока эмуллирует чтение затем добавим реальные
        # специально подробно расписываю
        new_value = current_value - 1
        return new_value
    else:
        return current_value

def read_chunk_size():
    #emulating zeroх ъ
    if(False):
        print(f"\t\tread_chunk_size: chunk size is empty ")
        return NetworkInput.CHUNK_SIZE_ZERO
    elif(True):
        print(f"\t\tread_chunk_size: chunk size is malformed ")
        return NetworkInput.MALFORMED

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
    if(False):
        return  0, NetworkInput.CHUNK_SIZE_ZERO
    else:
        return 10, NetworkInput.CHUNK_SIZE_GREATER_ZERO

def read_chunk_data(value):
    print(f"emulating readin chunk data: read {value} cut out one byte" )
    if(value > 0):
        return value - 1, NetworkInput.CHUNK_DATA_FLOW
    else:
        print("Now all chunks are read goint to Data empty")
        return 0, NetworkInput.CHUNK_DATA_EMPTY

def expect_chunk_crlf():
    print(f"emulating valid crlf to be received")
    return NetworkInput.CRLF_VALID



def parseae_headers(http_row_data):
    #normalize header names
    return http_row_data

def prep_headers(http_row_data):
    state = State.PARSE_HEADERS
    headers = parse_headers(http_row_data) # прошлись по заголовкам собрали их
    #content_legnth = (TRANSFER_ENCODING in headers, headers.get(CONTENT_HEADER))
    content_legnth = 0
    network_input, current_value = convert_row_http_to_state_input(content_legnth)
    return (network_input, current_value)


def convert_row_http_to_state_input(content_length_headers):
#    print("convert")
 #   print(content_length_headers)
    
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

