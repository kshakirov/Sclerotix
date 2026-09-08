

import requests
import json

# Данные, которые отправляем
data = { "name" : [i * 10 for i in range(4096)]}


# Преобразуем в JSON-строку
json_data = json.dumps(data)

# Преобразуем в байты для подсчета длины
bytes_data = json_data.encode('utf-8')

# Формируем заголовки
headers = {
    "Content-Type": "application/json",
    "Content-Length": str(len(bytes_data)),  # Автоматический подсчет длины

}

# Отправляем запрос
response = requests.post(
    'http://localhost:8090/id/2',
    headers=headers,
    data=bytes_data  # Важно: передаем байты, не json!
)

#print(response.status_code)
#print(response.json())


#response = requests.post('http://localhost:8090/no/2', json.dumps({"payload": [i * 10 for i in range(10000)]}))
