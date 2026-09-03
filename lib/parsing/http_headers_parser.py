from enum import Enum
from array import array
from math import floor,ceil


class HeaderState(Enum):
    METHOD=1
    REQURI=2
    REQVERSION=3
    HEADER_NAME=4
    HEADER_VALUE=5
    EXPECT_CRLF=6
    EXPECT_END_LF=9
    SUCCESS = 7
    ERROR=8


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
                 state=HeaderState.EXPECT_CRLF
            case HeaderState.REQVERSION:
                counter+=1
            case HeaderState.EXPECT_CRLF if input_fragment[counter]==10:
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
            case HeaderState.HEADER_NAME if input_fragment[counter] == 13:
                counter += 1
                state= HeaderState.EXPECT_END_LF
                #пока не сьедаю все байты только для теста
            case HeaderState.EXPECT_END_LF if input_fragment[counter]==10:
                counter += 1
                state=HeaderState.SUCCESS
                
            case HeaderState.HEADER_NAME:
                counter += 1
            case HeaderState.HEADER_VALUE if input_fragment[counter]==13:
                offset_table.insert(next_offset_id, counter + input_offset)
                next_offset_id += 1
                state = HeaderState.EXPECT_CRLF
                counter += 1
            case HeaderState.HEADER_VALUE:
                counter += 1
            case HeaderState.SUCCESS:
                break
            case _:
                HeaderState.ERROR
                state= HeaderState.ERROR
                break

    return input_offset + counter, offset_table, state, next_offset_id


def cmp_ascii_one_by_one(b_template, b_candidate):
      if b_template == b_candidate:
            return True
      else:
            if b_template > b_candidate:
                  if b_template - 32 == b_candidate:
                        return True

            return False
def cmp_header_names(template, buffer, start, end):
      if len(template) != end - start:
            return False
      else:
            for i in range(len(template)):
                  if not cmp_ascii_one_by_one(template[i],buffer[start + i]):
                        return False
            return True
      

def get_headers(offset_table, payload, template):
    base = 6 
    for i in range(floor((len(offset_table) -  base) /4)):
        r = base + i*4
        if cmp_header_names(template, payload, offset_table[r], offset_table[r + 1]):
            return offset_table[r + 2], offset_table[r + 3]
                  
    return None, None
