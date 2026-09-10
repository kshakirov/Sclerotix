import socket
import lib.utils.utils as u
import lib.parsing.http_parse_automaton as robot
import lib.parsing.factory as f
import asyncio

global tasks

response = "HTTP/1.1 200 OK\r\n\r\n"
error_response = "HTTP/1.1 500 Internal Server Error\r\n\r\n"

def get_if_exception(task):
    # Проверяем, есть ли исключение
    try:
        # Попытка получить результат — если была ошибка, она выбросится здесь
        result = task.result()
        print(f"Успешно: {result}")
    except Exception as e:
        # Если была ошибка — ловим и выводим
        print(f" Ошибка в задаче: {e}")



class Res:
    def __init__(self, data):
        self.headers = []
        self.body
    def addHeader(header_dict):
        self.headers.append(header_dict)
        
class Req:
    def __init__(self):
        self.headers = []
        self.body = ""
    def get_headers():
        return self.headers
    


def handle_method_and_url():
    pass




    
async def handle_req(so, routes, loop):
        print("starting")
        try:
            feed = f.make_streaming_request_parser()
            status = f.ParserResult.NEED_MORE_DATA
            while status == f.ParserResult.NEED_MORE_DATA:
                data  = await loop.sock_recv(so, 1028)
                if data == b"":
                    print(f"No More data")
                    break
                status,arena = feed(data)
                if status == f.ParserResult.ERROR:
                    break
                print(status)
            if status == f.ParserResult.BODY_PARSING_FINISHED:
                sent = await loop.sock_sendall(so, bytes(response,'utf8'))
                print("finishing ")

            else:
                sent = await loop.sock_sendall(so, bytes(error_response,'utf8'))
            so.close()
        except Exception as  e:
            print(f"Exception is {e}")
            #should be error msg
            sent = await loop.sock_sendall(so, bytes(error_response,'utf8'))
        finally:
            so.close()


    
async def accept_connections_and_create_task(so,loop,routes, tasks):
    print("create")
    
    while True:
        print(tasks)
        print("waiting")
        conn, addr = await loop.sock_accept(so)
        print("socket")
        task = asyncio.create_task(handle_req(conn,routes,loop))
        tasks.add(task)

        task.add_done_callback(get_if_exception)
    

def start_server(host, port, routes):
    addr = (host, port)
    s = socket.create_server(addr)
    loop = asyncio.new_event_loop()
    s.listen(5)
    s.setblocking(False)
    tasks = set()
    loop.create_task(accept_connections_and_create_task(s,loop,routes, tasks))
    
    loop.run_forever()
    
    s.close()
           
