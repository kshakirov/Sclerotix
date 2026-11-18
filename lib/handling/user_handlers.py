import lib.parsing.http_headers_parser as hp
def get(routes, path):
    def decorator(func):
        routes[(hp.Methods.GET, path)] = func
        return func
    return decorator

def post(routes, path):
    def decorator(func):
        routes[(hp.Methods.POST, path)] = func
        return func
    return decorator

def put(routes, path):
    def decorator(func):
        routes[(hp.Methods.PUT, path)] = func
        return func
    return decorator


def route(routes, methods, path):
    def decorator(func):
        for method in methods:
            routes[(method, path)] = func
        return func
    return decorator
        
