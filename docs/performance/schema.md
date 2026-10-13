# Performance data schema

## Сырая выборка Vegeta

`vegeta encode -to=csv` создаёт CSV без заголовка. Колонки имеют фиксированный порядок:

| № | Поле | Единица |
|---:|---|---|
| 1 | Unix timestamp | ns |
| 2 | HTTP status code | integer |
| 3 | request latency | ns |
| 4 | bytes out | bytes |
| 5 | bytes in | bytes |
| 6 | error | text |
| 7 | response body | base64 |
| 8 | attack name | text |
| 9 | sequence number | integer |

Файл `samples.csv` является первичным материалом. Агрегаты всегда должны быть воспроизводимы из него.

## Локальный summary.csv

Одна строка соответствует одному независимому прогону одного request template.

| Поле | Смысл |
|---|---|
| `started_at_utc` | начало прогона в ISO 8601 UTC |
| `date_utc` | дата для группировки серий |
| `commit` | полный Git commit |
| `tag` | tag, если измеряется релиз |
| `dirty` | было ли рабочее дерево изменено |
| `host_id` | устойчивое имя испытательной машины |
| `python_version` | версия CPython |
| `vegeta_version` | версия Vegeta |
| `request_id` | идентификатор канонического запроса |
| `method` | GET, POST или PUT |
| `path` | request-target |
| `body_bytes` | размер тела запроса |
| `expected_status` | ожидаемый HTTP-статус |
| `rate_rps` | заданная интенсивность |
| `duration_s` | заданная длительность |
| `workers` | начальное число workers Vegeta |
| `connections` | лимит idle connections Vegeta |
| `keepalive` | режим повторного использования соединений |
| `run_index` | номер независимого прогона в серии |
| `sample_n` | фактическое число наблюдений |
| `valid` | допускается ли прогон к сравнению |
| `success_ratio` | доля успешных запросов |
| `mean_ns` | средняя latency |
| `stddev_ns` | выборочное стандартное отклонение latency, делитель `n - 1` |
| `min_ns` | минимум latency |
| `p50_ns` | медиа latency, nearest-rank |
| `p90_ns` | 90-й percentile, nearest-rank |
| `p95_ns` | 95-й percentile, nearest-rank |
| `p99_ns` | 99-й percentile, nearest-rank |
| `max_ns` | максимум latency |
| `throughput_rps` | фактически завершённые запросы в секунду |
| `raw_csv` | относительный путь к `samples.csv` |
| `notes` | причина исключения или существенные условия |

Все latency хранятся целыми наносекундами. Перевод в микросекунды или миллисекунды выполняется только при построении отчёта.

## metadata.env

Минимальный набор:

```text
STARTED_AT_UTC=
GIT_COMMIT=
GIT_TAG=
GIT_DIRTY=
HOST_ID=
KERNEL=
PYTHON_VERSION=
VEGETA_VERSION=
REQUEST_ID=
RATE=
DURATION=
WORKERS=
CONNECTIONS=
KEEPALIVE=
ULIMIT_NOFILE=
NOTES=
```

Если условие способно повлиять на результат, но не представлено отдельной колонкой, оно записывается в `NOTES`.
