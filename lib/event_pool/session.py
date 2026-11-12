import socket
import select
from typing import Dict, Any
import lib.parsing.factory as f
import lib.handling.handler as router

SESSION_TYPE_ACCEPT=0
STATE_ACCEPTED=0

STATE_WAIT_READ = 1
STATE_WAIT_WRITE = 2
STATE_YIELD = 3
STATE_DONE= 4
STATE_ERROR = 5
STATE_WAIT_HANDLE = 7

def init(host,port,quant):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(quant)
    server_socket.setblocking(False)
    server_fd = server_socket.fileno()
    return server_socket, server_fd


    
def session_step(session):
    return session["step"]()

def create_accept_session(server_socket,server_fd,sessions):
    session = {}
    sessions[server_fd]= session
    session["type"]= SESSION_TYPE_ACCEPT
    def accept_step():
        client_socket, client_addr = server_socket.accept()
        client_socket.setblocking(False)
        c_fd = client_socket.fileno()
        return STATE_ACCEPTED, c_fd, (client_socket, client_addr) 
    session["step"]  = accept_step
    session["queued"] = False


def create_client_session(sessions, c_fd, socket_data):
    (client_socket, client_addr) = socket_data
    session = {
        "socket": client_socket,
        "addr": client_addr,
        "feed": f.make_streaming_request_parser(),
        "response": None,
        "ctx": {},
        "data":{ #just declaring for clarity 
            "status": None,
            "arena":None,
            "recognizing_data":None,
            "handler": None,
            "response": None
        }
        
    }
    sessions[c_fd] = session
    def read_step():
        try:
            session["socket"].recv(1024) #must be quant here
            session["data"]["status"],session["data"]["arena"],session["data"]["recognizing_data"] = session['feed'](data)
            if recognizing_data['url']['done']:
                url = recognizing_data['url']
                handler, params = resolve_handler(
                    memoryview(url['buffer'])[:url['length']],
                    recognizing_data['methods']['guess']
                )
                session["data"]['handler'] = handler
                session['ctx']['params'] = params
                session["step"] = handle_step
                return STATE_WAIT_HANDLE
            return STATE_WAIT_READ
        except BlockingIOError:
            pass
        except ConnectionResetError:
            clean_up_closed_connection(fd)
    def write_step():
        sock = session["socket"]
        pending_response = session['response']

        if pending_response:
            try:
                sent_bytes = sock.send(pending_response)
                if sent_bytes < len(pending_response):
                    session['response'] = pending_response[sent_bytes:]
                else:
                    # Ответ полностью ушёл — закрываем соединение (Keep-Alive сделаем позже)
                    clean_up_closed_connection(fd)
            except BlockingIOError:
                pass
            except ConnectionResetError:
                clean_up_closed_connection(fd)
    def done_step():
        pass
    def error_step():
        pass
    def handle_step():
        if session["data"]["status"] == f.ParserResult.NEED_MORE_DATA:
            if session["data"].get('handler'):
                session['data']['handler'](recognizing_data, arena, False, session['ctx'])
                session["step"] = read_step
                return STATE_WAIT_READ
        elif status == f.ParserResult.ERROR:
                #clean_up_closed_connection(fd) later to
            session["step"] = error_step
            return STATE_ERROR

        elif status == f.ParserResult.BODY_PARSING_FINISHED:
            if session['data'].get('handler'):
                session['data']['response'] = session['handler'](recognizing_data, arena, True, session['ctx'])
            session["step"] = write_step    
            return STATE_WAIT_WRITE
                
        
    session["read_step"]= read_step
    session["write_step"] = write_step
    session["handle_step"] = handle_step
    session["step"] = session["read_step"]
