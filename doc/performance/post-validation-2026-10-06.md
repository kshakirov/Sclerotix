# POST validation after Content-Length fix — 2026-10-06

Цель: проверить исправление, которое ограничило разбор десятичных цифр областью
значения конкретного заголовка `Content-Length`. До исправления удалённая Vegeta
добавляла `X-Vegeta-Seq`, его цифры ошибочно увеличивали длину тела, все сессии
ждали несуществующие байты и удерживали Arena.

## Условия

- Host: `pmd-pims-aio`.
- Commit: `ed0b7cb` на ветке `hash`.
- Request: `POST /index.html`, тело 16 bytes.
- Transport: loopback.
- Keep-alive: false.
- Sclerotix: CPU 3, `ACCEPT_BUDGET=64`.
- Vegeta: CPU `4,5,10,11`, workers 10, connections 100.
- Storm workers: stopped.
- Длительность каждого прогона: 10 seconds.

## Результаты

| Rate | Requests | Throughput | Success | Mean | P50 | P95 | P99 | Max | RSS after run |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2,500 | 25,000 | 2,500.22 | 100% | 0.217 ms | 0.272 ms | 0.297 ms | 0.312 ms | 0.658 ms | 12.8 MiB |
| 5,000 | 49,999 | 4,999.99 | 100% | 0.354 ms | 0.367 ms | 0.574 ms | 0.636 ms | 1.415 ms | 13.1 MiB |

Одиночный запрос удалённой Vegeta также завершился `HTTP 200`. До исправления тот
же клиент не получал ни одного ответа даже при `1 RPS`, потому что
`X-Vegeta-Seq` искажал `content_length`.

Эти два прогона являются проверкой исправления, а не статистическим POST
baseline: на каждой интенсивности выполнен только один прогон.

Сырые данные находятся на `pmd-pims-aio`:

```text
~/repos/Sclerotix/var/performance/raw/2026-10-06/post_index_16b/content-length-fix-2500rps-run-001/
~/repos/Sclerotix/var/performance/raw/2026-10-06/post_index_16b/content-length-fix-5000rps-run-001/
```
