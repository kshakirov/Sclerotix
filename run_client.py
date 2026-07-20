import requests
import json

response = requests.get('http://localhost:8090/tell/id', {'status': 1})
response.status_code




response = requests.post('http://localhost:8090/no/id', json.dumps([i for i in range(100)]))
