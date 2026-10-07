# Canonical performance requests

Канонический запрос нельзя незаметно менять после появления baseline. Изменение метода, пути, заголовков или тела создаёт новый `request_id`.

## get_index_empty

```http
GET /index.html HTTP/1.1
Host: 127.0.0.1:8080
Connection: close
```

- Body: отсутствует.
- Vegeta targets: `requests/get_index_empty.targets`.
- Expected status в `run_performance_server.py`: `200`.

## post_index_16b

```http
POST /index.html HTTP/1.1
Host: 127.0.0.1:8080
Content-Type: application/octet-stream
Content-Length: 16
Connection: close

Testing handler\n
```

- Body: `requests/bodies/body-16b.txt`.
- Размер: ровно 16 bytes, включая LF.
- Vegeta targets: `requests/post_index_16b.targets`.
- Expected status: `200`.

## put_index_1k

```http
PUT /index.html HTTP/1.1
Host: 127.0.0.1:8080
Content-Type: application/octet-stream
Content-Length: 1024
Connection: close

<1024 bytes from body-1k.txt>
```

- Body: `requests/bodies/body-1k.txt`.
- Размер: ровно 1024 bytes.
- Vegeta targets: `requests/put_index_1k.targets`.
- Expected status в `run_performance_server.py`: `200`.

## put_index_5k

```http
PUT /index.html HTTP/1.1
Host: 127.0.0.1:8080
Content-Type: application/octet-stream
Content-Length: 5120
Connection: close

<5120 bytes from body-5k.txt>
```

- Body: `requests/bodies/body-5k.txt`.
- Размер: ровно 5120 bytes.
- Vegeta targets: `requests/put_index_5k.targets`.
- Expected status в `run_performance_server.py`: `200`.
- При `recv(1024)` тело не может быть получено за одно чтение. Точные границы чтений TCP не гарантируются.

До измерения каждый request template проверяется отдельно. Если сервер ещё не содержит соответствующий маршрут, серия не считается performance baseline.
