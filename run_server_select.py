import socket
import select
from typing import Dict, Any
import lib.parsing.factory as f


def run_event_loop(host: str = "127.0.0.1", port: str = 8080):
    response = b"HTTP/1.1 200 OK\r\n\r\n"
    # 1. Создаем мастер-сокет
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(1024)
    
    # КРИТИЧЕСКО СУЩЕСТВЕННО: Переводим в неблокирующий режим
    server_socket.setblocking(False)

    # Таблица сессий: fd -> session dict (здесь потом будут буферы и feed())
    sessions: Dict[int, Dict[str, Any]] = {}

    # Списки для select
    inputs = [server_socket] #потом поменяем дорого список
    outputs = []
    errors = [server_socket]

    print(f"[Sclerotix Core] Event Loop started on {host}:{port}")

    try:
        while True:
            # Блокируемся только до появления первого сетевого события
            readable, writeable, exceptional = select.select(inputs, outputs, errors)

            for s in readable:
                if s is server_socket:
                    # Новое подключение!
                    client_socket, client_addr = server_socket.accept()
                    client_socket.setblocking(False)
                    
                    fd = client_socket.fileno()
                    inputs.append(client_socket)
                    
                    # Инициализируем минимальную сессию под этот fd 
                    sessions[fd] = {
                        "socket": client_socket,
                        "addr": client_addr,
                        "feed": f.make_streaming_request_parser(),
                        "response": None

                        
                    }
                    print(f"[+] Client connected: fd={fd}, addr={client_addr}")

                else:
                    # Прилетели данные от существующего клиента
                    fd = s.fileno()
                    
                    # Пробуем вычитать сырые байты (пока без Zero-Copy, чисто проверка связи)
                    try:
                        data = s.recv(1024)
                        if data:
                            print(f"[data] Read {len(data)} bytes from fd={fd}")
                            # На следующем наношаге сюда встанет session['feed'](data)!
                            status, arena = sessions[fd]['feed'](data)
                            if status == f.ParserResult.ERROR:
                                print("Error")
                                print(status)
                            if status == f.ParserResult.BODY_PARSING_FINISHED:
                                print("finishing, ready to send response ")
                                inputs.remove(s)
                                #this one only for the time being see in for writabe
                                outputs.append(sessions[fd]['socket'])
                                sessions[fd]['response'] = response
                                #sessions[fd]['socket'].sendall(response)
                                #s.close()
                               # del sessions[fd]
                        else:
                            # Клиент закрыл соединение (FIN)
                            print(f"[-] Client disconnected: fd={fd}")
                            inputs.remove(s)
                            s.close()
                            del sessions[fd]
                    except ConnectionResetError:
                        print(f"[!] Connection reset: fd={fd}")
                        inputs.remove(s)
                        s.close()
                        del sessions[fd]

            for s in exceptional:
                fd = s.fileno()
                print(f"[!] Exception on fd={fd}")
                if s in inputs:
                    inputs.remove(s)
                s.close()
                sessions.pop(fd, None)
            for s in writeable:
                fd = s.fileno()
                print(f" Writeable  on fd={fd}")
                response = sessions[fd]['response']
                print(f" the response to send later {response}")
                outputs.remove(s)
                
                sent_bytes = s.send(response)
                #here we must check weather all bytes are sent if not repeat in the next iteration
                s.close()

    except KeyboardInterrupt:
        print("\n[Sclerotix Core] Stopping server...")
    finally:
        server_socket.close()

if __name__ == "__main__":
    run_event_loop()
