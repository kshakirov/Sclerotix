example =b'GET /tell?status=1 HTTP/1.1\r\nHost: localhost:8080\r\nUser-Agent: python-requests/2.34.2\r\nAccept-Encoding: gzip, deflate\r\nAccept: */*\r\nConnection: keep-alive\r\n\r\n'

example =b'POST /tell?status=1 HTTP/1.1\r\nHost: localhost:8080\r\nUser-Agent: python-requests/2.34.2\r\nAccept-Encoding: gzip, deflate\r\nAccept: */*\r\nConnection: keep-alive\r\n\r\n'

import re

default_delimitter = re.compile(b'\r\n')
pair_delimitter = re.compile(b': ')

def parse_http_req_split(req,):
    return default_delimitter.split(req)


def parse_http_req_objs(pairs, dict):
   # pairs = str(pairs_b)
   # print(pairs)
    if(len(pairs) ==0):
        return dict
    else: 
        p = pair_delimitter.split(pairs[0])
        if(len(p) ==2):
#            print(p[0])
            dict[p[0]] =  p[1]
        return parse_http_req_objs(pairs[1:],dict)
        
def parse_status(status):
    pattern = r"(GET|POST) (?P<url>.+) HTTP"
    req = {"method": None, "url": ""}
    for i in ['GET','POST','PUT', 'DELETE']:
        if i in status:
            req['method']=i
            break
    match = re.search(pattern, status)
    req['url'] = match.group("url")
    return req

    
def parse_http_req(data):
    parts = parse_http_req_split(data);
    status = parse_status(parts[0].decode('utf8'))
    return status, parse_http_req_objs(parts, {})
    
    

    
parse_http_req(example)
