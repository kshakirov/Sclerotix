import socket
import select
from typing import Dict, Any
import lib.parsing.factory as f

def stupid_universal_handler(arena_chunk):
    pass

handlers = {'universal_hanlder': stupid_universal_handler}

def run_event_loop(host: str = "127.0.0.1", port: int = 8080, handlers=handlers):
    response = b"HTTP/1.1 200 OK\r\n\r\n"
    RESPONSE_VIEW = memoryview(response)

    # 1. Создаем мастер-сокет
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(1024)
    server_socket.setblocking(False)

    server_fd = server_socket.fileno()

    # 2. Создаем объект epoll
    epoll = select.epoll()
    # Регистрируем мастер-сокет на входящие соединения (EPOLLIN)
    epoll.register(server_fd, select.EPOLLIN)

    # Таблица сессий: fd -> session dict
    sessions: Dict[int, Dict[str, Any]] = {}

    def clean_up_closed_connection(fd: int):
        if fd in sessions:
            try:
                epoll.unregister(fd)
            except Exception:
                pass
            sock = sessions[fd]["socket"]
            sock.close()
            sessions.pop(fd, None)

    print(f"[Sclerotix Epoll Core] Event Loop started on {host}:{port}")

    try:
        while True:
            # Опрашиваем ядро (timeout -1 или 1 сек)
            events = epoll.poll(1)

            for fd, event in events:
                # ----------------------------------------------------
                # A. Новое подключение на мастер-сокете
                # ----------------------------------------------------
                if fd == server_fd:
                    while True:
                        try:
                            client_socket, client_addr = server_socket.accept()
                            client_socket.setblocking(False)
                            c_fd = client_socket.fileno()

                            # Регистрируем клиентский сокет в epoll
                            epoll.register(c_fd, select.EPOLLIN)

                            sessions[c_fd] = {
                                "socket": client_socket,
                                "addr": client_addr,
                                "feed": f.make_streaming_request_parser(),
                                "response": None,
                                "handler": handlers['universal_hanlder']
                            }
                        except BlockingIOError:
                            # Все входящие соединения вычитаны
                            break

                # ----------------------------------------------------
                # B. Ошибка или разрыв соединения
                # ----------------------------------------------------
                elif event & (select.EPOLLHUP | select.EPOLLERR):
                    clean_up_closed_connection(fd)

                # ----------------------------------------------------
                # C. Прилетели данные от клиента (EPOLLIN)
                # ----------------------------------------------------
                elif event & select.EPOLLIN:
                    session = sessions.get(fd)
                    if not session:
                        continue
                    
                    sock = session["socket"]
                    try:
                        data = sock.recv(1024)
                        if data:
                            status, arena = session['feed'](data)

                            if status == f.ParserResult.NEED_MORE_DATA:
                                if arena and session.get('handler'):
                                    session['handler'](arena)

                            elif status == f.ParserResult.ERROR:
                                clean_up_closed_connection(fd)

                            elif status == f.ParserResult.BODY_PARSING_FINISHED:
                                if arena and session.get('handler'):
                                    session['handler'](arena)

                                session['response'] = RESPONSE_VIEW
                                # Переключаем epoll сокет с чтения (EPOLLIN) на запись (EPOLLOUT)
                                epoll.modify(fd, select.EPOLLOUT)

                        else:
                            # Client FIN
                            clean_up_closed_connection(fd)

                    except (ConnectionResetError, BlockingIOError):
                        clean_up_closed_connection(fd)

                # ----------------------------------------------------
                # D. Готовность сокета к записи ответа (EPOLLOUT)
                # ----------------------------------------------------
                elif event & select.EPOLLOUT:
                    session = sessions.get(fd)
                    if not session:
                        continue

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
                        except (ConnectionResetError, BlockingIOError):
                            clean_up_closed_connection(fd)

    except KeyboardInterrupt:
        print("\n[Sclerotix Core] Stopping epoll server...")
    finally:
        epoll.unregister(server_fd)
        epoll.close()
        server_socket.close()

if __name__ == "__main__":
    run_event_loop()
