# GET baseline на pmd-pims-aio — 2026-10-06

## Профиль

```text
request:     GET /index.html
rate:        10000 RPS
duration:    10 s
runs:        5
keepalive:   false
workers:     10
connections: 100
transport:   loopback
Sclerotix:   CPU 3
Vegeta:      CPU 4,5,10,11
Storm:       workers stopped
```

Между прогонами Sclerotix перезапускался, а `TIME_WAIT` возвращался к фоновому
уровню. Все запросы получили `HTTP 200`; ошибок транспорта не было.

## Прогоны

| Run | Requests | Throughput | Mean | P50 | P95 | P99 | Max |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 99,993 | 9,999.99 | 0.322 ms | 0.167 ms | 0.822 ms | 0.897 ms | 2.123 ms |
| 2 | 100,000 | 9,999.99 | 0.376 ms | 0.271 ms | 0.891 ms | 0.985 ms | 3.242 ms |
| 3 | 100,000 | 10,000.03 | 0.361 ms | 0.277 ms | 0.821 ms | 0.894 ms | 1.368 ms |
| 4 | 100,000 | 10,000.95 | 0.359 ms | 0.273 ms | 0.816 ms | 0.885 ms | 1.594 ms |
| 5 | 99,999 | 9,999.93 | 0.412 ms | 0.121 ms | 0.821 ms | 2.003 ms | 29.413 ms |

## Объединённая выборка

```text
sample_n:  499992
mean:       0.366 ms
stddev:     0.669 ms
min:        0.085 ms
p50:        0.215 ms
p95:        0.842 ms
p99:        0.933 ms
max:       29.413 ms
success:  100%
```

Пятый прогон содержит редкий хвост до 29 ms, но p95 и общий p99 остаются ниже
1 ms. Прогон не исключён: функциональных ошибок и изменения условий не
зафиксировано.

Сырые данные находятся на `pmd-pims-aio`:

```text
~/repos/Sclerotix/var/performance/raw/2026-10-06/get_index_empty/baseline_remote_10k_10s/
```

Попытка `20000 RPS` не является измерением предела Sclerotix: при
`keepalive=false` локальный диапазон исходящих портов был практически исчерпан,
Vegeta не смогла сформировать заданную интенсивность.
