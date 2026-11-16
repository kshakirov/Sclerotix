"""Run against an already started event_pool.py on localhost:8080."""
import socket


header = (
    b"POST /index.html HTTP/1.1\r\nHost: localhost\r\n"
    b"Content-Length: 4\r\nConnection: close\r\n\r\n"
)


def check_response(client):
    response = b""
    while part := client.recv(4096):
        response += part
    assert response.startswith(b"HTTP/1.1 200 OK\r\n"), response


with socket.create_connection(("127.0.0.1", 8080), timeout=3) as first:
    first.sendall(header + b"ab")
    print("A: sent 2 of 4 body bytes")
    with socket.create_connection(("127.0.0.1", 8080), timeout=3) as second:
        second.sendall(header + b"1234")
        check_response(second)
        print("B: received 200 while A is incomplete")
    first.sendall(b"cd")
    check_response(first)
    print("A: sent remaining bytes and received 200")
