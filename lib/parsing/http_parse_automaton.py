import random


from enum import Enum
from lib.parsing.utils import parse_chunk_data, get_next_chunk
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

class TestBody(Enum):
    GET = 1
    POST_FIXED= 2
    POST_CHUNKED_WHOLE = 3



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
            print("\tnext_state: tansition to Read Chunk Data ")
            return State.READ_CHUNK_DATA, NetworkInput.CHUNK_DATA_FLOW, current_values

        case State.READ_CHUNK_DATA if current_input == NetworkInput.READING_FIXED_DATA and current_values > 0 :
            print("Third Case")
            #values = read_bytes_from_content(current_values)
            return State.READ_CHUNK_DATA, current_input, current_values
        case State.READ_CHUNK_DATA if current_input == NetworkInput.READING_FIXED_DATA and current_values ==0 :
            print("0 bytes")
            return State.SUCCESS,None,None
        case State.READ_CHUNK_DATA if current_input == NetworkInput.CHUNK_DATA_FLOW and current_values > 0 :
            print(f"\tnext_state: state is Read Chunk Data in_put  > 0 :{current_values} ")
#            value, in_put = read_chunk_data(current_values)
            return State.READ_CHUNK_DATA, current_input, current_values
        case State.READ_CHUNK_DATA if current_input == NetworkInput.CHUNK_DATA_FLOW and current_values == 0 :
            #            value, in_put = read_chunk_data(current_values)
            print(f"\tnext_state: state is Read Chunk Data, All data in chunk is read wating for CHUNK CRLF")
#            in_put = expect_chunk_crlf()
            print("\t\tnext_state: transition to Expect Chunk CRLF ")
            return State.EXPECT_CHUNK_CRLF, NetworkInput.CHUNK_DATA_EMPTY, current_values

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
    state,  in_put, in_value, http_data = state_tuple
    print(f"http_data is {http_data}")
    buffer = b""
    buffer_pointer = 0
    counter = 0
    while  counter < 32:
        counter +=1 # времено
        #for i in range(0,10):

        print(f"run_engine: Entering Loop: state: {state}, in_put: {in_put}, in_value: {in_value}")
        match state:
            case State.PARSE_HEADERS if in_put == None and http_data:
                

                if(http_data[2]==TestBody.GET):
                    state = State.SUCCESS
                    print("Empty GET request")
                
                    continue
                elif(http_data[2]==TestBody.POST_FIXED):
                    print(f"Parsing header analyzing.., getting buffer to read {http_data}")
                    buffer = http_data[1]
                    state = State.PARSE_HEADERS
                    in_put=NetworkInput.HEADERS_PARSED_CONTENT_LENGTH
                    in_value = len(buffer)
                    print("POST FIXED REQ ")
                     
                    #continue
                
                elif(http_data[2] == TestBody.POST_CHUNKED_WHOLE):
                    print(f"Parsing header analyzing.., it is Chunked Post Whole  getting buffer to read {http_data}")
                    buffer = http_data[1]
                    print(buffer)
                    print("POST CHUNKED WHOLE ")
                    state = State.PARSE_HEADERS
                    in_put=NetworkInput.HEADERS_PARSED_CHUNKED
#                    in_value = len(buffer)
  #                  break
                    
            
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
                in_put, in_value, buffer_pointer = read_chunk_size(buffer, buffer_pointer, http_data)
                print(f"run_engine: new  in_put is {in_put} in_value is {in_value}, buffer_pointer is [{buffer_pointer}] ")
                
#                break
                
            case State.READ_CHUNK_DATA if in_put == NetworkInput.CHUNK_DATA_FLOW:
                print(f"run_engine: state  is READ CHUNK DATA: in_put is {in_put} in_value is {in_value} ")
                in_value, buffer_pointer = read_chunk_variable_length(in_value, buffer_pointer, buffer)
                pass
            case State.EXPECT_CHUNK_CRLF:
                print(f"run_engine: state  is EXPECT CHUNK CRLF: in_put is {in_put} in_value is {in_value} ")
                state, in_put = expect_chunk_crlf()
                in_value = None
                pass
            case State.READ_CHUNK_DATA if in_put == NetworkInput.READING_FIXED_DATA:
                print("run_engine: Reading chunks of fixed length")
                bytes_left_to_read = read_chunk_fixed_length(in_value, buffer,buffer_pointer)
                state = State.READ_CHUNK_DATA
                in_put = NetworkInput.READING_FIXED_DATA
                in_value = bytes_left_to_read
                
                
                pass
            case _:
                print("run_engine: state is Default  Nothing Found,  running again state is {} network is {} looping  ...".format(state, in_put))
                

              #                  state,value, i_nput = newstate,new_value, network_input
        state,  in_put, in_value =next_state(state, in_put, in_value)

                  
    return


def read_chunk_fixed_length(in_value, buffer, buffer_pointer):
    print(f"\t\tread_chunk_fixed_length in_value is {in_value}  buffer length is {len(buffer)}, buffer pointer is {buffer_pointer}")
    buffer_pointer = len(buffer) - in_value
    if(in_value > 0):
        #пока эмуллирует чтение затем добавим реальные
        # специально подробно расписываю

        print(f"\t\tread _chunk_fixed_length: read buffer[{buffer_pointer}] = {buffer[buffer_pointer]}")

        return in_value - 1
    else:
        return in_value

def read_chunk_size(buffer,buffer_pointer,  http_data):

    i = 0
    hex_str = ""
    while buffer[i] != 0x0D :
        print(chr(buffer[i]))
        hex_str += str(chr(buffer[i]))
        i += 1
        buffer_pointer = i

    print(f"\t\tread_chun_size: hex str is {int(hex_str, 16)}, buffer_pointer points to [{buffer_pointer}] byte")
    return NetworkInput.CHUNK_SIZE_GREATER_ZERO, int(hex_str, 16), buffer_pointer
    # print(f"\t\tread_chunk_size: counter {counter} value {bytes}")
    # if counter > 20 :
    #     print(f"\t\tread_chunk_size: chunk size is empty ")
    #     return NetworkInput.CHUNK_SIZE_ZERO, None
    # elif(False):
    #     print(f"\t\tread_chunk_size: chunk size is malformed ")
    #     return NetworkInput.MALFORMED, None
    # else:
    #     print(f"\t\tread_chunk_size: chunk size is 8 ")
    #     return NetworkInput.CHUNK_SIZE_GREATER_ZERO, 8


def read_chunk_variable_length(current_value, buffer_pointer, buffer):
    print(f"\t\tread_chunk_variable_length:  in_value is {current_value}")
    if(current_value > 0):
        # пока просто читаю не склдадываю в  буфер для проброса дальше
        buffer_pointer += 1
        print(f"\t\tread_chunk_variable_length:  reading byte from buffer   at [{buffer_pointer}]  byte is {chr(buffer[buffer_pointer])}") 
        new_value = current_value - 1
        return new_value, buffer_pointer
    else:
        return current_value, buffer_pointer


def expect_chunk_crlf():
    print(f"\t\texpect_chunk_crlf: emulating valid crlf to be received")
    return State.EXPECT_CHUNK_CRLF, NetworkInput.CRLF_VALID
    
    
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




