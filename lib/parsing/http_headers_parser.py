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
def parse_req_header(payload):
    state =HeaderState.METHOD
    offset_table = array('i') # на время только 
    counter =0
    while counter < len(payload):
        match state:
            case HeaderState.METHOD if payload[counter] == 32:
                 offset_table.insert(0,0)
                 offset_table.insert(1, counter)
                 offset_table.insert(2, counter + 1)
                 counter+=1
                 state=HeaderState.REQURI
                 
            case HeaderState.METHOD:
                counter += 1;
                # здесь будет защита от некорректного метода или попытки ддос атаки 
            case HeaderState.REQURI if payload[counter]==32:
                 offset_table.insert(3,counter)
                 offset_table.insert(4, counter + 1)
                 counter+=1
                 state=HeaderState.REQVERSION

            case HeaderState.REQVERSION if payload[counter]==13:
                 offset_table.insert(5,counter)
                 counter+=1
                 state=HeaderState.EXPECT_CLRF
            case HeaderState.EXPECT_CLRF if payload[counter]==10:
                 offset_table.insert(6,counter + 1)
                 counter+=1
                 state=HeaderState.HEADER_NAME
            
            case _:
                counter +=1

    return offset_table


payload =  b"POST /api/data HTTP/1.1\r\n"
raw_get_request = (
    b"GET /api/v1/status HTTP/1.1\r\n"
    b"Host: localhost:8080\r\n"
    b"User-Agent: SclerotixClient/1.0\r\n"
    b"Accept: */*\r\n"
    b"\r\n"
)

table = parse_req_header(payload)
print(table)
