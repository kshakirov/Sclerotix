# ThinkPad P51 local performance host

Снимок исходной конфигурации: 2026-10-06. Значения только прочитаны; sysctl,
лимиты и governor не изменялись.

## CPU и память

- CPU: Intel Core i7-7820HQ, 1 socket, 4 физических ядра, 8 логических CPU.
- SMT-пары: `0+4`, `1+5`, `2+6`, `3+7`.
- Кэш: L1d 128 KiB, L1i 128 KiB, L2 1 MiB, L3 8 MiB.
- Частота: 800–3900 MHz, `intel_pstate`, governor `powersave`.
- RAM: 31 GiB.
- Swap: 8 GiB; на момент снимка занято около 6 GiB.
- NUMA: один узел, CPU `0-7`.

Динамическая частота и текущее использование swap должны фиксироваться для каждой
серии: они могут увеличить разброс результатов.

## CPU affinity для локального теста

Чтобы Vegeta не делила физическое ядро с однопоточным сервером:

```text
Sclerotix: CPU 0
CPU 4:    свободен — SMT-сосед CPU 0
Vegeta:   CPU 1-3,5-7
```

Выделение серверу CPU 0, а Vegeta всех остальных `1-7` не обеспечивает изоляцию:
CPU 4 является вторым аппаратным потоком того же физического ядра.

## ОС и лимиты

```text
OS: Ubuntu kernel 7.0.0-30-generic x86_64
ulimit -n: 1048576
fs.file-max: 9223372036854775807
net.ipv4.ip_local_port_range: 32768 60999
net.ipv4.tcp_tw_reuse: 2
net.core.somaxconn: 4096
net.ipv4.tcp_max_syn_backlog: 2048
net.ipv4.tcp_fin_timeout: 60
net.ipv4.tcp_max_tw_buckets: 131072
```

Диапазон локальных портов содержит примерно 28 тысяч портов и ограничивает
локальную генерацию новых TCP-соединений без keep-alive. Sclerotix сейчас вызывает
`listen(1024)`, поэтому фактический backlog приложения ниже `somaxconn`.

## Инструменты

- Vegeta установлена локально; сборка сообщает runtime `go1.27.1 linux/amd64`,
  но не сообщает номер версии и commit.
- Доступны `taskset`, `pidstat` и `perf`.

## Правило использования

Перед серией фиксировать load average, доступную память, swap, число TCP-сокетов,
частоты CPU и фактический достигнутый rate Vegeta. Sysctl не менять как часть
обычного baseline: изменённые параметры образуют отдельную конфигурацию
эксперимента.
