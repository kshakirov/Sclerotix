

import requests
import json
import random


port = 18082
# Данные, которые отправляем
data = { "name" : "Testing handler"}


# Преобразуем в JSON-строку
json_data = json.dumps(data)
 
# Преобразуем в байты для подсчета длины
bytes_data = json_data.encode('utf-8')

# Формируем заголовки
headers = {
    "Content-Type": "application/json",
    "Content-Length": str(len(bytes_data)),  # Автоматический подсчет длины

}


response = requests.get(
    f"http://localhost:{port}/user/list",
    headers=headers,
    data=bytes_data  # Важно: передаем байты, не json!
)




# Отправляем запрос
response = requests.post(
    f"http://localhost:{port}/index.html",
    headers=headers,
    data=bytes_data  # Важно: передаем байты, не json!
)

#print(response.status_code)
#print(response.json())


#response = requests.post('http://localhost:8090/no/2', json.dumps({"payload": [i * 10 for i in range(10000)]}))
def generate_chunks():
    for i in range(10):
        chunk = bytearray(1028)
        for y in range(1028):
            chunk[y]= random.randint(0,255)
        yield chunk
        
response = requests.post(
    f"http://localhost:{port}/generator/1",

    data=generate_chunks()  # Важно: передаем байты, не json!
)
