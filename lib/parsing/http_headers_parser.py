from enum import Enum
from array import array

class HeaderState(Enum):
    METHOD=1
    REQURI=2
    REQVERSION=3
    HEADER_NAME=4
    HEADER_VALUE=5
    EXPECT_CLRF=6
    SUCCESS = 7
    ERROR=8

#пока предполагаем что это все придет одним куском
def parse_req_header(input_fragment, input_offset, offset_table, state, next_offset_id):
    #state =HeaderState.METHOD
    #offset_table = array('i') # на время только
    #next_offset_id =6
    counter = 0
    while counter < len(input_fragment):
        match state:
            case HeaderState.METHOD if input_fragment[counter] == 32:
                 offset_table.insert(0,0)
                 offset_table.insert(1, counter + input_offset)
                 offset_table.insert(2, counter + 1 +input_offset)
                 counter+=1
                 state=HeaderState.REQURI
                 
            case HeaderState.METHOD:
                counter += 1;
                # здесь будет защита от некорректного метода или попытки ддос атаки 
            case HeaderState.REQURI if input_fragment[counter]==32:
                 offset_table.insert(3,counter + input_offset)
                 offset_table.insert(4, counter + 1 + input_offset)
                 counter+=1
                 state=HeaderState.REQVERSION
            case HeaderState.REQURI:
                counter+=1 

            case HeaderState.REQVERSION if input_fragment[counter]==13:
                 offset_table.insert(5,counter + input_offset)
                 counter+=1
                 state=HeaderState.EXPECT_CLRF
            case HeaderState.REQVERSION:
                counter+=1
            case HeaderState.EXPECT_CLRF if input_fragment[counter]==10:
                 offset_table.insert(next_offset_id, counter + 1 + input_offset)
                 counter+=1
                 next_offset_id += 1
                 state=HeaderState.HEADER_NAME
            case HeaderState.HEADER_NAME if input_fragment[counter]==58:
                 offset_table.insert(next_offset_id, counter + input_offset)
                 next_offset_id += 1
                 offset_table.insert(next_offset_id, counter + 1 + input_offset)
                 next_offset_id += 1
                 state = HeaderState.HEADER_VALUE
                 counter += 1
            case HeaderState.HEADER_NAME if input_fragment[counter] == 10:
                counter += 1
                state= HeaderState.SUCCESS
                #пока не сьедаю все байты только для теста
            case HeaderState.HEADER_NAME:
                counter += 1
            case HeaderState.HEADER_VALUE if input_fragment[counter]==13:
                offset_table.insert(next_offset_id, counter + input_offset)
                next_offset_id += 1
                state = HeaderState.EXPECT_CLRF
                counter += 1
            case HeaderState.HEADER_VALUE:
                counter += 1
            case HeaderState.SUCCESS:
                break
            case _:
                HeaderState.ERROR
                break

    return input_offset + counter, offset_table, state, next_offset_id


