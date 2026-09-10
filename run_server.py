from lib.socket_server import start_server



def process_req(req,res):
    print("This is req handler template")
    print(f"The req object {req}")




route = {"route": "/tell/id", "req": process_req, "res": None}

start_server("", 8090, [route])


