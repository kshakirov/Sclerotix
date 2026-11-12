import select
from collections import deque
import lib.event_pool.session as s


print("Evnet pool")

sessions = {}

server_sock, sock_fd = s.init("127.0.0.1",8080,1024)
s.create_accept_session(server_sock,sock_fd,sessions)

BUDGET= 2


run_queue = deque()
epoll = select.epoll()
epoll.register(sock_fd, select.EPOLLIN)
while True:
    timeout = 0 if len(run_queue)> 0 else -1
    events = epoll.poll(timeout)
    for fd, event in events:
        session = sessions.get(fd)
        if session and  not session["queued"]:
            session["queued"] = True
            run_queue.append(session)
        else:
            # create session accept, read write, user session
            print(f"There is still no session for fd {fd} and event {event}")

    for _ in range(BUDGET):
        if not run_queue:
            break
        session = run_queue.popleft()
        session["queued"] = False
        if session["type"]== s.SESSION_TYPE_ACCEPT:
            action, cliend_socket_fd,socket_data  = s.session_step(session)
            if action == s.STATE_ACCEPTED:
                s.create_client_session(sessions,cliend_socket_fd,socket_data)
                epoll.register(cliend_socket_fd, select.EPOLLIN)
                print(f"All done {sessions}")
                exit()
        if action == s.STATE_WAIT_READ:
            epoll.modify(session["fd"],  select.EPOLLIN)
        elif action == s.STATE_WAIT_WRITE:
            epoll.modify(session["fd"], select.EPOLLOUT)
        elif action == s.STATE_WAIT_HANDLE:
            session["queued"] = True
            run_queue.append(session)
        elif action in (s.STATE_DONE, s.STATE_ERROR):
            epoll.unregister(session["fd"])
            session_close(session)
            del sessions[session["fd"]]
        
    
