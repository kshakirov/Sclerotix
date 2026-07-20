print("Creating the automaton")


from enum import Enum

class State(Enum):
    PARSE_HEADERS = 1
    EXPECT_CHUNK_SIZE= 2
    READ_CHUNK_DATA = 3
    SUCCESS= 4
    ERROR = 5

class NetworkInput(Enum):
     CHUNK_SIZE_GREATER_ZERO =1 
     CHUNK_SIZE_ZERO=2
     DATA_ARRIVED=3
     MALFORMED=4
     READING_FIXED_DATA=5


CONTENT_HEADER= "content-Length"
TRANSFER_ENCODING ="transfer-Encoding"


    



def convert_row_http_to_state_input(content_length_headers):
    match content_length_headers:
        case (True, None): TRANSFER_ENCODING, 0
        case (True, c) if c > 0: TRANSFER_ENCODING, c
        case (None, 0): CONTENT_HEADER, 0
        case (None, c)  if c > 0:  CONTENT_HEADER, c
        case _ : None, None


# as Hal suggested the name is
def transition(current_state, current_values, current_input):
    match current_state:
        case State.PARSE_HEADERS:
            return State.EXPECT_CHUNK_SIZE
        case State.EXPECT_CHUNK_SIZE if current_input == NetworkInput.CHUNK_SIZE_ZERO:
            print(f"NOTHING TO READ FROM HTT P BODY QUTTING ...")
            return State.SUCCESS
        case State.EXPECT_CHUNK_SIZE if current_input== NetworkInput.MALFORMED:
            print("ERROR: JUNK")
            return State.ERROR, None
        case State.EXPECT_CHUNK_SIZE if current_input == NetworkInput.CHUNK_SIZE_GREATER_ZERO:
            return (State.READ_CHUNK_DATA, current_values, NetworkInput.READING_FIXED_DATA)
        case State.READ_CHUNK_DATA  if current_values == 0 and  current_input == NetworkInput.READING_FIXED_DATA:
            return 
        

        case State.PARSE_HEADERS if current_input == NetworkInput.DATA_ARRIVED:
            print(f"TRANSITION TO READING")
            return (State.READ_CHUNK_DATA, current_values)

        case State.PARSE_HEADERS if True:
            print("")
        case _ : print("NO RULE WORKED, SEE ERRORS")

def parse_headers(http_row_data):
    #normalize header names
    return http_row_data
        

def parse_http_content(http_row_data):
    state = State.PARSE_HEADERS
    headers = parse_headers(http_row_data)
    content_legnth = (TRANSFER_ENCODING in headers, headers.get(CONTENT_HEADER))
    netword_intput, current_value = convert_row_http_to_state_input(content_legnth)
    for i in range(0,1000):
        newstate, new_value =transition(state, current_value, network_input)
        match newstate:
            case State.SUCCESS :
                break #do someting 
            case State.ERROR:
                break
            case _ :
                state = newstate
                current_value = new_value

    #do someting to finish
    return
