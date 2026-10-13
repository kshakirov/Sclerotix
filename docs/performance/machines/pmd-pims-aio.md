# pmd-pims-aio performance host

Снимок конфигурации: 2026-10-06.

- CPU: AMD EPYC 4245P, 6 физических ядер / 12 логических CPU.
- SMT-пары: `0+6`, `1+7`, `2+8`, `3+9`, `4+10`, `5+11`.
- Частота: 600–5484 MHz, `amd-pstate-epp`, governor `powersave`.
- RAM: 62 GiB; во время разведки доступно около 34 GiB.
- Swap: 1 GiB, практически свободен.
- Kernel: Ubuntu `6.8.0-101-generic`.
- Python: 3.12.3.
- Vegeta: 12.13.0, установлена в `~/.local/bin/vegeta`.
- Soft limit открытых файлов по умолчанию: 1024; для Sclerotix-сессии baseline
  использовался `ulimit -n 65535`.
- `ip_local_port_range`: `32768–60999`.
- `tcp_tw_reuse`: 2.

Для baseline Storm workers были остановлены. Служебные Storm daemon-процессы,
ZooKeeper, Elasticsearch и остальные сервисы машины не останавливались.

CPU affinity:

```text
Sclerotix: CPU 3
CPU 9:    не используется тестом — SMT-сосед CPU 3
Vegeta:   CPU 4,5,10,11
```

Генератор и сервер работают на одной машине через `127.0.0.1`, поэтому baseline
измеряет сервер вместе с локальным TCP-стеком, без внешней сети.
