import socket
import select
from typing import Dict, Any
import lib.parsing.factory as f
import lib.handling.handler as router

SESSION_TYPE_ACCEPT=0
STATE_ACCEPTED=0


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
        "ctx": {}
        
    }
    sessions[c_fd] = session
    def read_step():
        pass
    def write_step():
        pass
    def handle_step():
        pass
    session["read_step"]= read_step
    session["write_step"] = write_step
    session["handle_step"] = handle_step
    session["step"] = session["read_step"]
