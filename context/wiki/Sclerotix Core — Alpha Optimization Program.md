# Sclerotix Core — Alpha Optimization Program

## Исходная точка

Alpha работает. Теперь задача — не менять семантику HTTP-машины, а уменьшить физическую стоимость её реализации.

Профилирование 50 000 запросов показало:

- ~67.3 млн allocations;
- ~10.44 GB суммарно выделенной памяти;
- ~35.8 MB peak live memory;
- ~1 345 allocations/request;
- ~209 KB allocated/request.

Главный источник — `http_headers_parser.py`.

Отдельно:

- `bytearray(64 * 1024)` Arena даёт около 3.28 GB allocation traffic на 50 000 соединений;
- `Enum` в побайтовом hot path создаёт огромный объём runtime work;
- CPU profile и memory profile независимо указывают на header parser.

Это не memory leak. Это **allocation/runtime churn**.

---

## Главный инвариант

> **Zero unjustified overhead.**

Не требуется искусственно уничтожать все allocations.

Требование другое:

**физическая работа программы должна быть оправдана семантикой машины.**

Для каждой структуры и операции задаём вопрос:

```text
Нужна вычислительной модели?
        |
   +----+----+
   |         |
  yes        no
   |         |
retain     remove
```

При этом оптимизация не должна менять семантику streaming HTTP automaton.

---

# 1. Enum → integer machine states

Сейчас состояния и сигналы представлены Python `Enum`:

```text
HeaderState
Methods
ParserRequiredHeaders
State
NetworkInput
ParserResult
...
```

В hot path это означает Python object/descriptor machinery там, где машине фактически нужны небольшие целые значения.

### Гипотеза

Заменить runtime states/signals на обычные integer constants.

Семантика автомата остаётся прежней:

```text
(state, input) → state'
```

Меняется только физическое представление `state`.

### Проверяем

- allocations/request;
- allocated bytes/request;
- CPU;
- throughput;
- latency distribution.

---

# 2. Удаление legacy `offset_table`

В header parser всё ещё существует:

```text
offset_table
array("i")
array.insert(...)
next_offset_id
```

Но архитектура Sclerotix уже отказалась от общего представления HTTP request через offsets.

Core распознаёт нужную информацию непосредственно в потоке.

Следовательно:

> `offset_table` больше не является частью модели.

Это не просто performance optimization, а удаление архитектурного долга.

### Действие

Удалить его из hot path полностью, если тесты подтверждают отсутствие оставшихся потребителей.

---

# 3. Убрать nested dictionaries из регистров автомата

Сейчас внутренние machine registers представлены конструкциями вида:

```text
stream_recognizing_data['headers']['fixed_content_mattch']
stream_recognizing_data['headers']['chunk_content_match']
stream_recognizing_data['methods']['matched_index']
stream_recognizing_data['url']['length']
```

Это удобное раннее представление, но физически дорого для побайтовой машины.

Такие значения являются не динамической структурой данных, а **фиксированными регистрами автомата**:

```text
method
method_match_index

url_length

content_length
content_length_match
transfer_encoding_match

recognition flags
...
```

### Гипотеза

Представить внутреннее состояние минимальными фиксированными полями/локальными регистрами.

Важно:

**внешний пользовательский интерфейс и внутреннее физическое представление машины — разные вещи.**

---

# 4. Inline method recognizer

Сейчас каждый byte метода проходит через:

```text
method_recognizer(...)
```

Функция:

- вызывается несколько раз на request;
- передаёт arguments;
- возвращает tuple;
- результат распаковывается вызывающей стороной.

Но method recognizer концептуально является частью перехода состояния `METHOD`.

### Гипотеза

Inline recognizer непосредственно в transition path.

Это менее красиво как Python decomposition, но потенциально ближе к физической машине:

```text
METHOD state
    ↓
byte
    ↓
transition
```

вместо:

```text
METHOD
    ↓
Python call
    ↓
tuple
    ↓
unpack
    ↓
transition
```

Проверить экспериментально.

---

# 5. Исследовать `find()` как lowering побайтового автомата

Это наиболее интересное направление.

Сейчас физическая реализация близка к:

```text
byte
 ↓
Python transition

byte
 ↓
Python transition

byte
 ↓
Python transition
```

Но значительная часть bytes не вызывает содержательно различных переходов.

Например, автомат часто просто ищет структурную границу:

```text
SP
:
CRLF
CRLFCRLF
```

`bytes.find()` / `bytearray.find()` выполняет поиск ниже Python interpreter loop.

Возможное lowering:

```text
logical byte transitions
        ↓
find structural boundary
        ↓
one Python-level transition
```

### Ключевой принцип

> Побайтовая семантика не требует побайтового Python execution.

Оптимизированная реализация должна быть **семантически эквивалентна** исходному streaming automaton.

### Ограничение

Fragmentation остаётся обязательной:

```text
fragment 1: Content-Leng
fragment 2: th: 16\r
fragment 3: \n
```

Нельзя ради `find()` превратить Sclerotix в buffered whole-request parser.

Поэтому `find()` рассматривается как ускорение переходов **внутри уже доступного fragment**, а состояние машины сохраняется между fragments.

---

# 6. Header recognition: отделить structure scanning от semantic recognition

Сейчас на каждом byte имени header одновременно выполняются:

```text
HTTP structure parsing
+
Content-Length recognition
+
Transfer-Encoding recognition
```

Исследовать разделение:

```text
input fragment
      ↓
structural scan
      ↓
interesting region
      ↓
semantic recognizer
```

Например, `find()` может находить structural delimiter, а специализированный recognizer работать только там, где действительно требуется распознавание.

Важно не возвращаться к:

```text
slice → bytes allocation → compare
```

Иначе выигрыш будет потерян с другой стороны.

---

# 7. Arena lifecycle

Сейчас каждый streaming parser немедленно создаёт:

```text
bytearray(64 * 1024)
```

Даже для body размером 16 bytes.

Измеренный эффект:

```text
50 000 × 65 536 ≈ 3.28 GB
```

Это allocation traffic, а не retained memory.

### Вопрос глубже размера Arena

Не просто:

```text
64 KiB → 4 KiB
```

а:

> **какую физическую функцию Arena вообще выполняет в современной streaming-модели Sclerotix?**

Core уже имеет контракт:

```text
input
  ↓
fragment
  ↓
handler
  ↓
fragment forgotten
```

Поэтому исследовать:

1. lazy Arena allocation;
2. меньшую bounded Arena;
3. reuse;
4. прямой view/range входного fragment;
5. полное устранение промежуточного body copy там, где lifetime это позволяет.

---

# 8. Body copy

Fixed-length body сейчас копируется:

```text
input buffer
     ↓
byte-by-byte Python loop
     ↓
Arena
     ↓
memoryview
     ↓
handler
```

Это подозрительный путь.

Идеальная модель:

```text
input fragment
      ↓
validated range/view
      ↓
handler
```

Но lifetime должен быть доказан.

Handler обязан закончить синхронное потребление fragment до следующего `feed()`.

Это отдельный эксперимент, а не механический refactoring.

---

# 9. Chunk-size parser без строк

Текущая реализация делает:

```text
byte
 ↓
chr
 ↓
str
 ↓
string concatenation
 ↓
int(..., 16)
```

Это прямо противоречит byte-oriented модели.

Chunk size естественно является числовым регистром:

```text
value = value * 16 + hex_digit
```

Следовательно, строковое промежуточное представление семантически не требуется.

Убрать его после основных header-path экспериментов.

---

# 10. Allocation timing

Не только размер allocation, но и **момент её возникновения** является частью архитектуры.

Например:

```text
accept
 ↓
create parser
 ↓
allocate Arena
```

означает, что TCP connection уже получает дорогое request-processing state до доказательства необходимости этого состояния.

Исследовать lazy materialization:

```text
connection
 ↓
minimal state
 ↓
actual requirement
 ↓
allocate required resource
```

---

# 11. Event-loop fairness

Нагрузочное тестирование уже показало возможность starvation при агрессивном accept-drain.

Инвариант Event Machine:

> Один источник готовности не должен бесконечно монополизировать один turn event loop.

Исследовать bounded work:

```text
accept budget
read budget
write budget
```

Это отдельная ось от parser optimization.

---

# Метод экспериментов

Не объединять оптимизации.

Для каждого изменения:

```text
Alpha baseline
      ↓
one change
      ↓
same workload
      ↓
CPU profile
memory profile
raw latency samples
throughput
      ↓
Agnostic-Inference-Engine
      ↓
Harper analysis
```

Agnostic отвечает:

> **Есть ли статистически различимый эффект и каков его размер?**

Harper отвечает:

> **Какая физическая цепочка породила этот эффект?**

Sclerotix отвечает:

> **Стоит ли новое физическое представление своей архитектурной цены?**

---

# Предварительный порядок

```text
Alpha baseline
      ↓
Enum → int
      ↓
remove offset_table
      ↓
machine registers vs nested dict
      ↓
inline recognizer
      ↓
find()-based transition lowering
      ↓
Arena/body-copy experiment
      ↓
chunk-size numeric parsing
      ↓
streaming URL hash
      ↓
Radix
```

Порядок может измениться по результатам профилирования.

---

# Критерий успеха

Мы не просто хотим получить больше RPS.

Цель исследования:

```text
semantic machine
       ↓
Python representation
       ↓
physical operations
       ↓
allocations / instructions / memory traffic
       ↓
latency / throughput
```

Каждая оптимизация должна либо убрать работу, которой нет в семантической машине, либо показать, почему эта работа неизбежна.

> **Сначала правильная машина. Затем минимальная физическая реализация этой машины.**

Alpha дала нам первую.

Теперь строим вторую.