import select
from collections import deque
import lib.event_pool.session as s
import lib.parsing.factory as f
from lib.handling.handler import make_router
from lib.handling.user_handlers import get,post,put

print("Evnet pool")

ROUTES={}

RESPONSE_OK = memoryview(
    b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"
)

@post(ROUTES, b"/index.html")
def handle_post(request_state, arena_fragment, finished, context):
    if arena_fragment:
        context["body_bytes"] = context.get("body_bytes", 0) + len(arena_fragment)
    if finished:
        return RESPONSE_OK

#ROUTES = {(f.hp.Methods.POST, b"/index.html"): handle_post}
@get(ROUTES,b"/user/list")
def test_get(header_data,  arena, finished, ctx):
    print(f"Working inside the handler, args are hd {len(header_data)}, arena len {len(arena)}, finished parsing {finished} ctx {len(ctx)}")
    if "work" in ctx:
        if ctx["work"] > 10:
            print("ctx working")
    else:
        ctx["work"] = 1
    return RESPONSE_OK

print(ROUTES)
resolve_handler = make_router(ROUTES)[0]
sessions = {}

server_sock, sock_fd = s.init("127.0.0.1",18082,1024)
s.create_accept_session(server_sock,sock_fd,sessions)

BUDGET= 128


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

    for _ in range(BUDGET):
        if not run_queue:
            break
        session = run_queue.popleft()
        session["queued"] = False
        if session["type"]== s.SESSION_TYPE_ACCEPT:
            action, cliend_socket_fd,socket_data  = s.session_step(session)
            if action == s.STATE_ACCEPTED:
                s.create_client_session(sessions,cliend_socket_fd,socket_data, resolve_handler)
                epoll.register(cliend_socket_fd, select.EPOLLIN)
        else:
            action  = s.session_step(session)
                
            if action == s.STATE_WAIT_READ:
                epoll.modify(session["socket_fd"],  select.EPOLLIN)
            elif action == s.STATE_WAIT_WRITE:
                epoll.modify(session["socket_fd"], select.EPOLLOUT)
            elif action == s.STATE_WAIT_HANDLE:
                session["queued"] = True
                run_queue.append(session)
            elif action in (s.STATE_DONE, s.STATE_ERROR):
                epoll.unregister(session['socket_fd'])
                s.session_step(session)
                del sessions[session["socket_fd"]]
        
    
