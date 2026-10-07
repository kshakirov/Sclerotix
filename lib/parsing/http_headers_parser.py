from enum import Enum
from lib.utils.hashing import OFFSET_BASIS, sx_hash

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
# TODO move headers to common types
class Methods(Enum):
    PUT=1
    POST=2
    PATCH=3
    HEAD=4
    DELETE=5
    GET=6
    Pstar=7

class ParserRequiredHeaders(Enum):
    CONTENT_LENGTH=b"content-length"
    TRANSFER_ENCODING=b"transfer-encoding"

def parse_req_header(input_fragment, input_offset, state, stream_recognizing_data):
    counter = 0
    while counter < len(input_fragment):
        match state:
            case HeaderState.METHOD if input_fragment[counter] == 32:
                 #an example
                 error, guess, matched_index = method_recognizer(input_fragment[counter], stream_recognizing_data['methods']['matched_index'], stream_recognizing_data['methods']['guess'])
                 if error:
                     state = error
                     break
                 stream_recognizing_data['handler']['hash'] =sx_hash(OFFSET_BASIS,stream_recognizing_data['methods']['guess'].value)
                 stream_recognizing_data['handler']['hash'] =sx_hash(stream_recognizing_data['handler']['hash'],0)

                 counter+=1
                 state=HeaderState.REQURI

            case HeaderState.METHOD:
                error, guess, matched_index = method_recognizer(input_fragment[counter], stream_recognizing_data['methods']['matched_index'], stream_recognizing_data['methods']['guess'])
                if error:
                    state = error
                    break
                else:
                    stream_recognizing_data['methods']['guess'] = guess
                    stream_recognizing_data['methods']['matched_index'] = matched_index
                counter += 1;
                # здесь будет защита от некорректного метода или попытки ддос атаки

            case HeaderState.REQURI if input_fragment[counter]==32:
                 counter+=1
                 state=HeaderState.REQVERSION
            case HeaderState.REQURI:
                i = stream_recognizing_data['url']['length']
                if i < stream_recognizing_data['config']['max_url_length']:
                    stream_recognizing_data['url']['buffer'][i] = input_fragment[counter]
                    stream_recognizing_data['url']['length'] = i + 1
                    stream_recognizing_data['handler']['hash'] =sx_hash(stream_recognizing_data['handler']['hash'],input_fragment[counter])
                else:
                    state = HeaderState.ERROR
                counter+=1

            case HeaderState.REQVERSION if input_fragment[counter]==13:
                 counter+=1
                 state=HeaderState.EXPECT_CRLF
            case HeaderState.REQVERSION:
                counter+=1
            case HeaderState.EXPECT_CRLF if input_fragment[counter]==10:
                 counter+=1
                 stream_recognizing_data['headers']['fixed_content_mattch'] =0
                 stream_recognizing_data['headers']['chunk_content_match'] =0
                 state=HeaderState.HEADER_NAME
            case HeaderState.HEADER_NAME if input_fragment[counter]==58:
                 state = HeaderState.HEADER_VALUE
                 counter += 1
                 stream_recognizing_data['headers']['current_header'] = None
                 if stream_recognizing_data['headers']['fixed_content_mattch']==14:
                     stream_recognizing_data['headers']['content_type'] = ParserRequiredHeaders.CONTENT_LENGTH
                     stream_recognizing_data['headers']['current_header'] = ParserRequiredHeaders.CONTENT_LENGTH
                 if stream_recognizing_data['headers']['chunk_content_match']==17 :
                     stream_recognizing_data['headers']['content_type'] = ParserRequiredHeaders.TRANSFER_ENCODING
                     stream_recognizing_data['headers']['current_header'] = ParserRequiredHeaders.TRANSFER_ENCODING

                 stream_recognizing_data['headers']['fixed_content_mattch'] = 0
                 stream_recognizing_data['headers']['chunk_content_match'] =0
                 stream_recognizing_data['headers']['fixed_content_failed_prefix']= False
                 stream_recognizing_data['headers']['chunk_content_failed_prefix']= False
            case HeaderState.HEADER_NAME if input_fragment[counter] == 13:
                counter += 1
                state= HeaderState.EXPECT_END_LF
                #пока не сьедаю все байты только для теста
            case HeaderState.EXPECT_END_LF if input_fragment[counter]==10:
                counter += 1
                state=HeaderState.SUCCESS

            case HeaderState.HEADER_NAME:
                #for simplicity
                fcm = stream_recognizing_data['headers']['fixed_content_mattch']
                ccm = stream_recognizing_data['headers']['chunk_content_match']
                #print(fcm, input_fragment[counter],ParserRequiredHeaders.CONTENT_LENGTH.value[fcm])
                if  fcm < 14 and (input_fragment[counter] == ParserRequiredHeaders.CONTENT_LENGTH.value[fcm] or input_fragment[counter] + 32 == ParserRequiredHeaders.CONTENT_LENGTH.value[fcm]) and not stream_recognizing_data['headers']['fixed_content_failed_prefix']:
                    stream_recognizing_data['headers']['fixed_content_mattch'] += 1
                else:
                    stream_recognizing_data['headers']['fixed_content_mattch'] =0
                    stream_recognizing_data['headers']['fixed_content_failed_prefix'] =True

                if  ccm < 17 and (input_fragment[counter] == ParserRequiredHeaders.TRANSFER_ENCODING.value[ccm] or input_fragment[counter] + 32 == ParserRequiredHeaders.TRANSFER_ENCODING.value[ccm]) and not stream_recognizing_data['headers']['chunk_content_failed_prefix']:
                    stream_recognizing_data['headers']['chunk_content_match'] += 1

                else:
                    stream_recognizing_data['headers']['chunk_content_match'] =0
                    stream_recognizing_data['headers']['chunk_content_failed_prefix'] =True


                counter += 1


            case HeaderState.HEADER_VALUE if input_fragment[counter]==13:
                stream_recognizing_data['headers']['current_header'] = None
                state = HeaderState.EXPECT_CRLF
                counter += 1
            case HeaderState.HEADER_VALUE:
                if stream_recognizing_data['headers']['current_header'] == ParserRequiredHeaders.CONTENT_LENGTH:
                    if input_fragment[counter] > 47 and input_fragment[counter] < 58:
                        stream_recognizing_data['headers']['content_length'] = stream_recognizing_data['headers']['content_length'] * 10 + input_fragment[counter] - 48


                counter += 1
            case HeaderState.SUCCESS:
                break
            case _:
                HeaderState.ERROR
                state= HeaderState.ERROR
                break

    return input_offset + counter, state, stream_recognizing_data



def method_recognizer(b, matched_index, guess):
    match matched_index:
        case 0:
            match b:
                case 80:
                    guess = Methods.Pstar
                case 71:
                    guess = Methods.GET
                case 72:
                    guess = Methods.HEAD
                case 68:
                    guess = Methods.DELETE
                case _:
                    return HeaderState.ERROR, None,None
        case 1 if guess == Methods.Pstar:
            match b:
                case 85:
                    guess = Methods.PUT
                case 79:
                    guess = Methods.POST
                case 65:
                    guess = Methods.PATCH
                case _:
                    return HeaderState.ERROR, None,None
        case 1:
            match b:
                case 69:
                    guess =guess
                case _:
                    return HeaderState.ERROR, None,None
        case 2:
            match b:
                case 84 if guess == Methods.GET:
                    guess = Methods.GET
                case 84 if guess == Methods.PUT:
                    guess = Methods.PUT
                case 76:
                    guess =guess
                case 65:
                    guess =guess
                case 83:
                    guess=guess
                case _:
                    return HeaderState.ERROR, None, None
        case 3:
            match b:
                case 84 if guess==Methods.POST:
                    guess = guess
                case 84:
                    return HeaderState.ERROR, None, None
                case 32 if guess==Methods.PUT or guess==Methods.GET:
                    guess = guess

        case 4:
            match b:
                case _ if guess==Methods.PUT or guess==Methods.GET:
                    return HeaderState.ERROR, None, None
                case 32 if guess==Methods.POST:
                    guess = guess
        case 5:
            match b:
                case _ if guess==Methods.POST:
                    return HeaderState.ERROR, None, None

        case 10:
            return HeaderState.ERROR, None, None
    matched_index += 1
    return None, guess, matched_index
