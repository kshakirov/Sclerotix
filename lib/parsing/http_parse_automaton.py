import random


from enum import Enum
from lib.parsing.utils import parse_chunk_data, get_next_chunk
class State(Enum):
    PARSE_HEADERS = 1
    EXPECT_CHUNK_SIZE= 2
    READ_CHUNK_DATA = 3
    SUCCESS= 4
    ERROR = 5
    EXPECT_CHUNK_CR=6
    EXPECT_CHUNK_LF=7
    READ_CHUNK_CR=8
    READ_CHUNK_LF=9

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
    CR_AFTER_SIZE_VALID=12
    CR_AFTER_DATA_VALID=14
    CR_AFTER_ZERO_VALID=15
    LF_AFTER_SIZE_VALID=16
    LF_AFTER_DATA_VALID=17
    LF_AFTER_ZERO_VALID=18
    TIMEOUT= 19

    


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
            return State.SUCCESS, None, None
        case State.PARSE_HEADERS if current_input == NetworkInput.HEADERS_PARSED_CONTENT_LENGTH:
            print("Second case")
            return (State.READ_CHUNK_DATA,  NetworkInput.READING_FIXED_DATA, current_values)
        case State.PARSE_HEADERS if current_input == NetworkInput.HEADERS_PARSED_CHUNKED:
            print("\tnext_state: transition to Expecting Chunk Size state")
            return State.EXPECT_CHUNK_SIZE, current_input, current_values

        # ===== expect chunk size 
        case State.EXPECT_CHUNK_SIZE if current_input == NetworkInput.CHUNK_SIZE_ZERO:
            print("\tnext_state: Nothing to read chunk size is zero waiting for CR mark")
            return State.EXPECT_CHUNK_CR, NetworkInput.CR_AFTER_ZERO_VALID, None
        case State.EXPECT_CHUNK_SIZE if current_input == NetworkInput.MALFORMED:
            print("\tnext_state: Chunk size malformed going to Eror")
            return State.ERROR,None,None
        case State.EXPECT_CHUNK_SIZE if current_input == NetworkInput.CHUNK_SIZE_GREATER_ZERO:
            print("\tnext_state: Chunk size greater zero wating for CR mark ")
            return State.EXPECT_CHUNK_CR, NetworkInput.CR_AFTER_SIZE_VALID, current_values
        case State.EXPECT_CHUNK_SIZE if current_input == NetworkInput.TIMEOUT:
            print("\tnext_state: Timout wating for Chunk size  going to Eror")
            return State.ERROR,None,None
        case State.EXPECT_CHUNK_SIZE if current_input == NetworkInput.CHUNK_DATA_EMPTY:
            print("\tnext_state: Nothing to read yet, no size waiting ... ")
            return State.EXPECT_CHUNK_SIZE, current_input, current_values

        ###################################### expect cr and lf #########################################
        case State.EXPECT_CHUNK_CR if current_input == NetworkInput.CR_AFTER_SIZE_VALID:
            return State.READ_CHUNK_CR,current_input,current_values
        case State.EXPECT_CHUNK_CR if current_input==NetworkInput.MALFORMED:
            return State.ERROR,current_input,current_values
        case State.EXPECT_CHUNK_CR if current_input==NetworkInput.CHUNK_DATA_EMPTY:
            return State.EXPECT_CHUNK_CR,current_input,current_values
        case State.EXPECT_CHUNK_CR if current_input==NetworkInput.CR_AFTER_ZERO_VALID:
            return State.READ_CHUNK_CR,current_input,current_values
        case State.EXPECT_CHUNK_CR if current_input == NetworkInput.TIMEOUT:
            return State.ERROR,current_input,current_values  
        case State.EXPECT_CHUNK_CR if current_input == NetworkInput.CR_AFTER_DATA_VALID:
            return State.READ_CHUNK_CR,current_input,current_values
        case State.EXPECT_CHUNK_LF if current_input == NetworkInput.CR_AFTER_DATA_VALID:
            return State.READ_CHUNK_LF,current_input,current_values  
        case State.EXPECT_CHUNK_LF if current_input == NetworkInput.CR_AFTER_SIZE_VALID:
            return State.READ_CHUNK_LF,current_input,current_values
        case State.EXPECT_CHUNK_LF if current_input == NetworkInput.CR_AFTER_ZERO_VALID:
            return State.READ_CHUNK_LF,current_input,current_values
        case State.EXPECT_CHUNK_CR if current_input == NetworkInput.LF_AFTER_ZERO_VALID:
            return State.READ_CHUNK_CR,current_input,current_values
        case State.EXPECT_CHUNK_LF if current_input == NetworkInput.LF_AFTER_ZERO_VALID:
            return State.READ_CHUNK_LF,current_input,current_values


  ################################### read chunks ################################

        
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
            return State.EXPECT_CHUNK_CR, NetworkInput.CR_AFTER_DATA_VALID, current_values
        
        case State.READ_CHUNK_DATA if current_input == NetworkInput.CHUNK_DATA_EMPTY :
            return State.READ_CHUNK_DATA, current_input,current_values

        case State.SUCCESS:
            return State.SUCCESS, None, None
        case _ :
            print("Failed to find Error ")
            return State.ERROR, None, None
        
        
# это операционный автомат он на вход получает сигнал начальный или вообще он запускается без сигнала
#потоуму что он запускается только с сигналом чтение заголовков 
# но пока временно для тестирования у буду передавть сюда состояиния
def run_engine(s, i_p,i_v, buffer, buffer_ptr, arena, arena_pointer):

    buffer_pointer = buffer_ptr
    state = s
    in_put = i_p
    in_value = i_v
    
    print(f"http_data is {buffer}")

    counter = 0
    while  counter < 32:
        counter +=1 # времено


        print(f"run_engine: Entering Loop: state: {state}, in_put: {in_put}, in_value: {in_value}")
        match state:
            case State.PARSE_HEADERS:
                pass
                    

            case State.SUCCESS :
                print("SUCCESS, finishing ...")
                return state,in_put, buffer_pointer, in_value, arena_pointer
            case State.ERROR:
                #do something
                print("ERROR")
                return state,in_put, buffer_pointer, in_value, arena_pointer

            case State.EXPECT_CHUNK_SIZE :
                print(f"run_engine: state  is EXPECT_CHUNK_SIZE: in_put is {in_put} in_value is {in_value} ")
                in_progress, state, in_put, in_value, buffer_pointer  = read_chunk_size(buffer, buffer_pointer, in_value)
                if in_progress:
                    return state, in_put,buffer_pointer, in_value, arena_pointer
                print(f"run_engine: new  in_put is {in_put} in_value is {in_value}, buffer_pointer is [{buffer_pointer}] ")
                

                pass
            case State.READ_CHUNK_DATA if in_put == NetworkInput.CHUNK_DATA_FLOW:
                print(f"run_engine: state  is READ CHUNK DATA: in_put is {in_put} in_value is {in_value} ")
                in_progress,  in_value, buffer_pointer, arena_pointer = read_chunk_variable_length(in_value, buffer_pointer, buffer, arena, arena_pointer)
                if in_progress:
                    return State.READ_CHUNK_DATA, NetworkInput.CHUNK_DATA_FLOW, buffer_pointer, in_value, arena_pointer
                pass

            case State.READ_CHUNK_CR  if in_put==NetworkInput.CR_AFTER_SIZE_VALID:
                print(f" run_engine: state  is EXPECT CHUNK CR and CR_AFTER_SIZE_IS VALID: in_put is {in_put} in_value is {in_value} ")
                in_progress, state, buffer_pointer = read_chunk_cr(buffer, buffer_pointer)
                if in_progress:
                    return State.READ_CHUNK_CR, in_put,buffer_pointer, in_value, arena_pointer
                
                pass
            case State.READ_CHUNK_CR  if in_put==NetworkInput.CR_AFTER_DATA_VALID:
                print(f" run_engine: state  is EXPECT CHUNK CR and CR_AFTER_DATA VALID: in_put is {in_put} in_value is {in_value} ")
                in_progress, state, buffer_pointer = read_chunk_cr_after_data(buffer, buffer_pointer)
                if in_progress:
                    return State.READ_CHUNK_CR, in_put,buffer_pointer, in_value, arena_pointer
                
                pass
            case State.READ_CHUNK_CR  if in_put==NetworkInput.CR_AFTER_ZERO_VALID:
                print(f" run_engine: state  is EXPECT CHUNK CR and CR_AFTER_ZERO VALID: in_put is {in_put} in_value is {in_value} ")
                in_progress, state, buffer_pointer = read_chunk_cr_after_data(buffer, buffer_pointer)
                if in_progress:
                    return State.READ_CHUNK_CR, in_put,buffer_pointer, in_value, arena_pointer
                
                pass
            case State.READ_CHUNK_CR  if in_put==NetworkInput.LF_AFTER_ZERO_VALID:
                print(f" run_engine: state  is EXPECT CHUNK CR and LF_AFTER_ZERO VALID: in_put is {in_put} in_value is {in_value} ")
                in_progress, state, buffer_pointer = read_chunk_cr_after_data(buffer, buffer_pointer)
                if in_progress:
                    return State.READ_CHUNK_CR, in_put,buffer_pointer, in_value, arena_pointer
                
                pass
            case State.READ_CHUNK_LF  if in_put==NetworkInput.CR_AFTER_SIZE_VALID:
                print(f" run_engine: state  is EXPECT CHUNK LF and CR_AFTER_SIZE_IS VALID: in_put is {in_put} in_value is {in_value} ")
                in_progress, state,in_put, buffer_pointer = read_chunk_lf(buffer, buffer_pointer)
                if in_progress:
                    return State.READ_CHUNK_LF, in_put,buffer_pointer, in_value, arena_pointer
                print(f"run_engine: state  is EXPECT CHUNK LF and CR_AFTER_SIZE_IS VALID:  in_value is {in_value} ")
                in_value = in_value
                pass

            case State.READ_CHUNK_LF  if in_put==NetworkInput.CR_AFTER_ZERO_VALID:
                print(f" run_engine: state  is EXPECT CHUNK LF and CR_AFTER_ZERO_IS VALID: in_put is {in_put} in_value is {in_value} ")
                in_progress, state,in_put, buffer_pointer = read_chunk_lf_after_zero(buffer, buffer_pointer)
                if in_progress:
                    return State.READ_CHUNK_LF, in_put,buffer_pointer, in_value, arena_pointer
                print(f"run_engine: state  is EXPECT CHUNK LF and CR_AFTER_ZERO VALID:  in_value is {in_value} ")
                in_value = in_value
                pass

            case State.READ_CHUNK_LF  if in_put==NetworkInput.LF_AFTER_ZERO_VALID:
                print(f" run_engine: state  is EXPECT CHUNK LF and LF_AFTER_ZERO_IS VALID: in_put is {in_put} in_value is {in_value} ")
                in_progress, state,in_put, buffer_pointer = read_chunk_lf_after_zero_final(buffer, buffer_pointer)
                if in_progress:
                    return State.READ_CHUNK_LF, in_put,buffer_pointer, in_value, arena_pointer
                print(f"run_engine: state  is EXPECT CHUNK LF and CR_AFTER_ZERO VALID:  in_value is {in_value} ")
                in_value = in_value
                pass
            case State.READ_CHUNK_LF  if in_put==NetworkInput.CR_AFTER_DATA_VALID:
                print(f" run_engine: state  is READ CHUNK LF and CR_AFTER_DATA VALID: in_put is {in_put} in_value is {in_value} ")
                in_progress, state,in_put, buffer_pointer = read_chunk_lf_after_data(buffer, buffer_pointer)
                if in_progress:
                    return State.READ_CHUNK_LF, in_put,buffer_pointer, in_value, arena_pointer
                print(f"run_engine: state  is READ CHUNK LF and CR_AFTER_DATA VALID:  in_value is {in_value} ")
                in_value = in_value
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
                

        print(f"run_engine: before calling next_state current value is  {in_value}")        
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

def read_chunk_size(buffer,buffer_pointer, current_value):
    current_value = current_value or ""
# checking buffer length always
    if buffer_pointer < len(buffer):
        size_digit = buffer[buffer_pointer]
        print(f"\t\tread_chunk_size: hex str is {size_digit}, buffer_pointer points to [{buffer[buffer_pointer]}] byte,")
        if size_digit != 0x0D:
            current_value += str(chr(size_digit))
            buffer_pointer += 1
            return False, State.EXPECT_CHUNK_SIZE, NetworkInput.CHUNK_DATA_EMPTY, current_value, buffer_pointer
        else:
            #buffer pointer remains the same
            #current_value += str(chr(size_digit))
            #current value that we have collected previously
            chunk_size = int(current_value, 16)
            # not yet checking malformed and error
            if chunk_size > 0:
                return False, State.EXPECT_CHUNK_CR, NetworkInput.CR_AFTER_SIZE_VALID, chunk_size, buffer_pointer
            else:
                return False, State.EXPECT_CHUNK_CR, NetworkInput.CR_AFTER_ZERO_VALID, chunk_size, buffer_pointer
    else:
        return True, State.EXPECT_CHUNK_SIZE, NetworkInput.CHUNK_DATA_EMPTY, current_value, buffer_pointer
        
    
        
            

def read_chunk_variable_length(current_value, buffer_pointer, buffer, arena, arena_pointer):
    if buffer_pointer < len(buffer) :
        print(f"\t\tread_chunk_variable_length:  in_value is {current_value}")
        if(current_value > 0):
            # пока просто читаю не склдадываю в  буфер для проброса дальше
            arena[arena_pointer] = buffer[buffer_pointer]
            print(f"\t\tread_chunk_variable_length:  reading byte from buffer   at [{buffer_pointer}]  byte is {chr(buffer[buffer_pointer])}")
            buffer_pointer += 1
            arena_pointer += 1
            new_value = current_value - 1
            return False, new_value, buffer_pointer, arena_pointer
        else:
            buffer_pointer += 1
            return False, current_value, buffer_pointer, arena_pointer
    else:
        return True,current_value, buffer_pointer, arena_pointer


def read_chunk_cr(buffer, buffer_pointer):
    if buffer_pointer < len(buffer):
        print(f"\t\tread_chunk_cr:  buffer is  {buffer} , buffer_pointer is {buffer_pointer}, current byte is {buffer[buffer_pointer]} valid cr to be received")

        if(buffer[buffer_pointer]==13):
            buffer_pointer += 1
            return False, State.EXPECT_CHUNK_LF, buffer_pointer
        else:
            return False, State.ERROR, buffer_pointer
    else:
        print(f"\t\tread_chunk_cr:  buffer is  {buffer} , buffer_pointer is {buffer_pointer} is larger than buffer returning to main handler")
        return True, None,buffer_pointer


def read_chunk_lf(buffer, buffer_pointer):
    if buffer_pointer < len(buffer):
        print(f"\t\tread_chunk_lf:  buffer is  {buffer} , buffer_pointer is {buffer_pointer}, current byte is {buffer[buffer_pointer]} valid lf to be received")

        if(buffer[buffer_pointer]==10):
            buffer_pointer += 1
            return False, State.READ_CHUNK_DATA, NetworkInput.CHUNK_DATA_FLOW,  buffer_pointer
        else:
            return False, State.ERROR,None,  buffer_pointer
    else:
        print(f"\t\tread_chunk_lf:  buffer is  {buffer} , buffer_pointer is {buffer_pointer} is larger than buffer returning to main handler")
        return True, None,NetworkInput.CR_AFTER_SIZE_VALID,buffer_pointer

def read_chunk_lf_after_zero(buffer, buffer_pointer):
    if buffer_pointer < len(buffer):
        print(f"\t\tread_chunk_lf_after_zero:  buffer is  {buffer} , buffer_pointer is {buffer_pointer}, current byte is {buffer[buffer_pointer]} valid lf to be received")

        if(buffer[buffer_pointer]==10):
            buffer_pointer += 1
            #for the time being
            return False, State.EXPECT_CHUNK_CR, NetworkInput.LF_AFTER_ZERO_VALID,  buffer_pointer
        else:
            return False, State.ERROR,None,  buffer_pointer
    else:
        print(f"\t\tread_chunk_lf:  buffer is  {buffer} , buffer_pointer is {buffer_pointer} is larger than buffer returning to main handler")
        return True, None,NetworkInput.CR_AFTER_ZERO_VALID,buffer_pointer

def read_chunk_lf_after_zero_final(buffer, buffer_pointer):
    if buffer_pointer < len(buffer):
        print(f"\t\tread_chunk_lf_after_zero_final:  buffer is  {buffer} , buffer_pointer is {buffer_pointer}, current byte is {buffer[buffer_pointer]} valid lf to be received")

        if(buffer[buffer_pointer]==10):
            buffer_pointer += 1
            #for the time being
            return False, State.SUCCESS, NetworkInput.LF_AFTER_ZERO_VALID,  buffer_pointer
        else:
            return False, State.ERROR,None,  buffer_pointer
    else:
        print(f"\t\tread_chunk_lf:  buffer is  {buffer} , buffer_pointer is {buffer_pointer} is larger than buffer returning to main handler")
        return True, None,NetworkInput.LF_AFTER_ZERO_VALID,buffer_pointer

    

def read_chunk_cr_after_data(buffer, buffer_pointer):
    if buffer_pointer < len(buffer):
        print(f"\t\tread_chunk_cr_after_data:  buffer is  {buffer} , buffer_pointer is {buffer_pointer}, current byte is {buffer[buffer_pointer]} valid cr to be received")

        if(buffer[buffer_pointer]==13):
            buffer_pointer += 1
            return False, State.EXPECT_CHUNK_LF, buffer_pointer
        else:
            return False, State.ERROR, buffer_pointer
    else:
        print(f"\t\tread_chunk_cr after data:  buffer is  {buffer} , buffer_pointer is {buffer_pointer} is larger than buffer returning to main handler")
        return True, None,buffer_pointer

def read_chunk_lf_after_data(buffer, buffer_pointer):
    if buffer_pointer < len(buffer):
        print(f"\t\tread_chunk_lf_after data valid:  buffer is  {buffer} , buffer_pointer is {buffer_pointer}, current byte is {buffer[buffer_pointer]} valid lf to be received")

        if(buffer[buffer_pointer]==10):
            buffer_pointer += 1
            return False, State.EXPECT_CHUNK_SIZE, NetworkInput.CHUNK_DATA_EMPTY,  buffer_pointer
        else:
            return False, State.ERROR,None,  buffer_pointer
    else:
        print(f"\t\tread_chunk_lf after data:  buffer is  {buffer} , buffer_pointer is {buffer_pointer} is larger than buffer returning to main handler")
        return True, None,NetworkInput.CR_AFTER_DATA_VALID,buffer_pointer



