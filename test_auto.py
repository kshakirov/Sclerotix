# Чистый GET-запрос без тела
from enum import Enum
import lib.parsing.http_parse_automaton as p
import lib.utils.utils as u
test_http_data = b"GET /index.html HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n"
post_fixed_data = b"POST /submit HTTP/1.1\r\nHost: localhost\r\nContent-Length: 5\r\n\r\nHello"
post_chunked_simple = b"POST /stream HTTP/1.1\r\nHost: localhost\r\nTransfer-Encoding: chunked\r\n\r\n5\r\nHello\r\n0\r\n\r\n"






# POST-запрос с фиксированным размером тела (14 байт)
mock_post_request = bytearray(
    b"POST /api/data HTTP/1.1\r\n"
    b"Host: localhost:8080\r\n"
    b"Content-Type: application/json\r\n"
    b"Content-Length: 14\r\n" # <--- Фиксированный размер тела
    b"\r\n"                  # Конец заголовков
    b'{"status":"ok"}'       # Ровно 14 байт полезной нагрузки
)

# Чистый GET-запрос без тела для обкатки побайтового парсера
mock_get_request = bytearray(
    b"GET /index.html HTTP/1.1\r\n"
    b"Host: localhost:8080\r\n"
    b"User-Agent: SclerotixTest/1.0\r\n"
    b"Accept: */*\r\n"
    b"\r\n"  # Пустая строка — финальный маркер конца запроса без тела
)

post_chunked_fragmented = [
    b"POST /stream HTTP/1.1\r\nHost: localhost\r\nTransfer-Encoding: chunked\r\n\r\n",
    b"5\r\n",
    b"Hel",
    b"lo\r\n",
    b"0\r\n\r\n"
]

#headers = u.parse_http_req(test_http_data)
#print(headers)
 #print("---")
#r = p.convert_row_http_to_state_input(headers)

#print(r)

mock_network_buffer = bytearray(
    b"8\r\n"          # Чанк 1: Размер 8 байт (в hex)
    b"12345678\r\n"    # Тело чанка 1 + CRLF
    b"0\r\n"          # Чанк 2: Размер 0 байт (терминальный)
    b"\r\n"           # Финальный CRLF конца тела
)
http_data = (mock_get_request,None, p.TestBody.GET)
http_data = (mock_post_request, b'{"status":"ok"}', p.TestBody.POST_FIXED)
http_data = (mock_network_buffer, mock_network_buffer, p.TestBody.POST_CHUNKED_WHOLE)
# Указатель операционного автомата (Регистр каретки EFSM)
buffer_pointer = 0


input_1 = (p.State.PARSE_HEADERS, p.NetworkInput.HEADERS_PARSED_EMPTY, None,http_data)
input_2 = (p.State.PARSE_HEADERS, p.NetworkInput.HEADERS_PARSED_CONTENT_LENGTH, 4,http_data)
input_3 = (p.State.PARSE_HEADERS, p.NetworkInput.HEADERS_PARSED_CHUNKED, None,http_data)
input_4 = (p.State.EXPECT_CHUNK_SIZE, p.NetworkInput.HEADERS_PARSED_CHUNKED, None,http_data)

input_11 = (p.State.PARSE_HEADERS, None, None,http_data)
input_22 = (p.State.PARSE_HEADERS, None, None,http_data)
#p.parse_http_content(input_1)

#p.parse_http_content(input_2)

#p.run_engine(input_3)
p.run_engine(input_11)

