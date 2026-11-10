import select
from collections import deque

print("Evnet pool")

sessions = {}

def session_step(s):
    pass

def session_close(s):
    pass
session = {
    "queued":False
}


BUDGET= 2


run_queue = deque()
epoll = select.epoll()
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
        action = session_step(session)
        if action == STATE_WAIT_READ:
            epoll.modify(session["fd"],  select.EPOLLIN)
        elif action == STATE_WAIT_WRITE:
            epoll.modify(session["fd"], select.EPOLLOUT)
        elif action == STATE_YIELD:
            session["queued"] = True
            run_queue.append(session)
        elif action in (STATE_DONE, STATE_ERROR):
            epoll.unregister(session["fd"])
            session_close(session)
            del sessions[session["fd"]]
        
    
