import socket
import select
from typing import Dict, Any
import lib.parsing.factory as f
import lib.handling.handler as router

SESSION_TYPE_ACCEPT=0
SESSION_TYPE_CLIENT=1
state_ACCEPTED=0

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


def create_client_session(sessions, c_fd, socket_data, routes):
    (client_socket, client_addr) = socket_data
    session = {
        "socket": client_socket,
        "socket_fd": c_fd,
        "addr": client_addr,
        "feed": f.make_streaming_request_parser(),
        "response": None,
        "type": SESSION_TYPE_CLIENT,
        "ctx": {},
        "resolve": router.make_router(routes)[0],
        "queued" : False,
        "data":{ #just declaring for clarity 
            "status": None,
            "arena":None,
            "recognizing_data":None,
            "handler": None,
            "response": None
        }
        
    }
    sessions[c_fd] = session

    def clean_up_closed_connection():

        try:
            epoll.unregister(session['socket_fd'])
        except Exception:
            pass
        sock = session["socket"]
        sock.close()
    
    def read_step():
        try:
            data = session["socket"].recv(1024) #must be quant here
            if data:
                session["data"]["status"],session["data"]["arena"],session["data"]["recognizing_data"] = session['feed'](data)
                if session["data"]["recognizing_data"]['url']['done']:
                    url = session["data"]["recognizing_data"]['url']
                    handler, params = session['resolve'](
                        memoryview(url['buffer'])[:url['length']],
                        session["data"]["recognizing_data"]['methods']['guess']
                    )
                    session["data"]['handler'] = handler
                    session['ctx']['params'] = params
                    session["step"] = handle_step
                    return STATE_WAIT_HANDLE
                return STATE_WAIT_READ
            else:
                #connection closed by client maybe
                session['step'] = error_step
                return STATE_ERROR
        except BlockingIOError:
            return STATE_WAIT_READ
        except ConnectionResetError:
            session['step'] = error_step
            return STATE_ERROR
    def write_step():
        sock = session["socket"]
        pending_response = session['data']['response']

        if pending_response:
            try:
                sent_bytes = sock.send(pending_response)
                if sent_bytes < len(pending_response):
                    session['data']['response'] = pending_response[sent_bytes:]
                    session['step'] = write_step
                    return STATE_WAIT_WRITE
                else:
                    # Ответ полностью ушёл — закрываем соединение (Keep-Alive сделаем позже)
                    session['step'] = done_step
                    return STATE_DONE
            except BlockingIOError:
                return STATE_WAIT_WRITE
            except ConnectionResetError:
                session['step'] = error_step
                return STATE_ERROR
    def done_step():
        clean_up_closed_connection()
    def error_step():
        clean_up_closed_connection()
    def handle_step():
        if session["data"]["status"] == f.ParserResult.NEED_MORE_DATA:
            if session["data"].get('handler'):
                session['data']['handler'](session['data']['recognizing_data'], session['data']['arena'], False, session['ctx'])
                session["step"] = read_step
                return STATE_WAIT_READ
        elif session["data"]['status'] == f.ParserResult.ERROR:
                #clean_up_closed_connection(fd) later to
            session["step"] = error_step
            return STATE_ERROR

        elif session["data"]['status'] == f.ParserResult.BODY_PARSING_FINISHED:
            if session['data'].get('handler'):
                session['data']['response'] = session['data']['handler'](session['data']['recognizing_data'], session['data']['arena'], True, session['ctx'])
            session["step"] = write_step    
            return STATE_WAIT_WRITE
                
        
    session["read_step"]= read_step
    session["write_step"] = write_step
    session["handle_step"] = handle_step
    session["step"] = session["read_step"]
