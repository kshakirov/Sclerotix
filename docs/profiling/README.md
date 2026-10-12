# Профилирование Sclerotix

Здесь мы накапливаем воспроизводимую методику, интерпретации и компактную статистику по работе сервера.

## Что храним в Git

- условия эксперимента: версия Python, порт, длительность и параметры нагрузки;
- агрегированные показатели: число запросов, latency, throughput, горячие функции и доли времени;
- выводы с разделением на наблюдение и интерпретацию;
- скрипты, необходимые для повторения эксперимента.

## Что храним только на машине

Сырые профили SpeedScope могут быть большими и зависят от конкретного запуска. Они сохраняются в:

```text
~/.local/state/sclerotix-profile/
```

Их не добавляем в Git. Значимые результаты переносим в `results.md` в агрегированном виде.

## CPU baseline

Запуск из корня проекта:

```bash
./docs/profiling/profile_cpu.sh 18082
```

Скрипт проверяет, что порт свободен и выше `10000`, запускает Sclerotix только на `127.0.0.1` и записывает 40-секундный профиль с частотой 100 сэмплов в секунду.

Профиль включает время ожидания в `epoll`: оно является частью поведения сервера и не должно исчезать из baseline.

## Нагрузка baseline

Во втором терминале:

```bash
./docs/profiling/load_baseline.sh 18082
```

Зафиксированный режим:

- `POST /index.html`;
- тело `0123456789abcdef` размером 16 байт;
- `5 000` запросов в секунду;
- `10` секунд;
- `Vegeta 12.13.0` с обязательным ограничением скорости.

Скрипт работает только с loopback-портом выше `10000`. Сырые `results.gob`, `report.json` и `samples.csv` сохраняются по принятой структуре в `var/performance/raw/`.

## Аллокации

В первом терминале:

```bash
./docs/profiling/profile_allocations.sh 18082
```

После нагрузки остановить сервер через `Ctrl-C`. Memray завершит сырой `.bin` в `~/.local/state/sclerotix-profile/`. Этот прогон предназначен для поиска источников аллокаций, а не для сравнения latency.

### Отчёты Memray

Короткий отчёт по последнему профилю без ручного поиска `.bin`:

```bash
./docs/profiling/report_allocations.py
```

По умолчанию выводятся только общий итог и аллокации из `enum.py`. Для другого
механизма достаточно передать часть пути или имени:

```bash
./docs/profiling/report_allocations.py hashing.py
```

Сравнение последнего профиля с конкретным baseline:

```bash
./docs/profiling/report_allocations.py enum.py --baseline /path/to/baseline.bin
```

Если baseline является предпоследним профилем, путь не нужен:

```bash
./docs/profiling/report_allocations.py enum.py --previous
```

Отчёт сам печатает таблицу `CURRENT`, таблицу `BASELINE` и дельту по каждой
строке выбранного механизма.

Ниже остаются команды для углублённого ручного анализа.

```bash
PROFILE_BIN="$(ls -1t "$HOME"/.local/state/sclerotix-profile/sclerotix-allocations-*.bin | head -n 1)"
PROFILE_MEMRAY="$HOME/.local/share/sclerotix-profile-venv/bin/memray"
```

`PROFILE_BIN` автоматически указывает на последний созданный профиль. Вручную
подставлять timestamp не требуется.

### Вопрос: сколько всего было аллокаций?

```bash
"$PROFILE_MEMRAY" stats -n 30 "$PROFILE_BIN"
```

Ответ находится в начале отчёта:

```text
Total allocations
Total memory allocated
Peak memory usage
```

Для сравнения двух реализаций основные показатели — `Total allocations` и
`Total memory allocated`. Если число запросов в прогонах различается, оба
показателя сначала делятся на фактическое число запросов.

### Вопрос: какие места создали основной allocation churn?

```bash
"$PROFILE_MEMRAY" stats -n 30 "$PROFILE_BIN"
```

Ответ находится в разделах:

```text
Top allocating locations (by size)
Top allocating locations (by number of allocations)
Top allocating modules
```

### Вопрос: какие функции определили пиковое потребление памяти?

```bash
"$PROFILE_MEMRAY" summary -r 50 "$PROFILE_BIN"
```

`summary` не отвечает на вопрос об общем числе аллокаций. Он показывает
распределение памяти, живой в выбранной точке отчёта.

### Вопрос: где создаются короткоживущие объекты?

```bash
"$PROFILE_MEMRAY" summary --temporary-allocations -r 50 "$PROFILE_BIN"
"$PROFILE_MEMRAY" tree --temporary-allocations "$PROFILE_BIN"
```

### Вопрос: как получить машиночитаемую сводку?

```bash
"$PROFILE_MEMRAY" stats -n 100 --json -o allocation-stats.json "$PROFILE_BIN"
```

Обычный flame graph Memray показывает память, живую на пике. Для интенсивного оборота короткоживущих объектов следует использовать `stats` и отчёты с `--temporary-allocations`. Режим `--leaks` отвечает на отдельный вопрос об объектах, оставшихся жить к завершению записи.
