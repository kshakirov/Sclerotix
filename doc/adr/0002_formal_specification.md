# 📓 Шаг 0002: Формальная спецификация и Верификация Ядра (nuXmv)

## 1. Алфавит Системы
Математическая модель ядра `Sclerotix` выражена в виде Детерминированного Конечного Автомата (DFA). Система оперирует строго ограниченными множествами состояний и сигналов.

### Состояния автомата ($\Sigma_{state}$)
* `PARSE_HEADERS`: Стартовый разбор текстовых заголовков HTTP.
* `EXPECT_CHUNK_SIZE`: Фаза «HTTP-глаз» — синтаксический поиск HEX-размера чанка.
* `READ_CHUNK_DATA`: Фаза «Слепца» — слепое вымывание байт с декрементом регистра.
* `EXPECT_CHUNK_CRLF`: Зачистка сервисного хвоста разделителя `\r\n`.
* `SUCCESS`: Терминальное состояние успешного завершения потока.
* `ERROR`: Терминальное состояние критического сбоя протокола.

### Алфавит входных сетевых сигналов ($\Sigma_{input}$)
* Разводка HEADERS: `HEADERS_PARSED_EMPTY`, `HEADERS_PARSED_CONTENT_LENGTH`, `HEADERS_PARSED_CHUNKED`.
* Разводка размеров: `CHUNK_SIZE_ZERO` (терминальный ноль), `CHUNK_SIZE_GREATER_ZERO`.
* Прокачка «Слепца»: `READING_FIXED_DATA` (монолит), `CHUNK_DATA_FLOW` (поток чанка), `CHUNK_DATA_EMPTY` (обнуление).
* Сервисные сигналы: `CRLF_VALID`, `MALFORMED`.

## 2. Верификационный код модели (Язык SMV)
Спецификация автомата для чекера моделей nuXmv, описывающая жёсткую детерминированную логику переключений:

```smv
MODULE main
VAR
    state : { PARSE_HEADERS, EXPECT_CHUNK_SIZE, READ_CHUNK_DATA, EXPECT_CHUNK_CRLF, SUCCESS, ERROR };
    input : { HEADERS_PARSED_EMPTY, HEADERS_PARSED_CONTENT_LENGTH, HEADERS_PARSED_CHUNKED,
              CHUNK_SIZE_ZERO, CHUNK_SIZE_GREATER_ZERO,
              READING_FIXED_DATA, CHUNK_DATA_FLOW, CHUNK_DATA_EMPTY,
              CRLF_VALID, MALFORMED };

ASSIGN
    init(state) := PARSE_HEADERS;

    next(state) := case
        -- Фиксация терминального успеха (Ликвидация тупика)
        state = SUCCESS                                               : SUCCESS; 

        -- 1. Фаза заголовков
        state = PARSE_HEADERS & input = HEADERS_PARSED_EMPTY          : SUCCESS;
        state = PARSE_HEADERS & input = HEADERS_PARSED_CONTENT_LENGTH : READ_CHUNK_DATA;
        state = PARSE_HEADERS & input = HEADERS_PARSED_CHUNKED        : EXPECT_CHUNK_SIZE;

        -- 2. Фаза ожидания размера чанка (HTTP-глаза)
        state = EXPECT_CHUNK_SIZE & input = CHUNK_SIZE_ZERO           : SUCCESS;
        state = EXPECT_CHUNK_SIZE & input = CHUNK_SIZE_GREATER_ZERO   : READ_CHUNK_DATA;
        state = EXPECT_CHUNK_SIZE & input = MALFORMED                 : ERROR;

        -- 3. Фаза чтения данных (Слепец)
        state = READ_CHUNK_DATA & input = READING_FIXED_DATA          : SUCCESS;
        state = READ_CHUNK_DATA & input = CHUNK_DATA_FLOW             : READ_CHUNK_DATA;
        state = READ_CHUNK_DATA & input = CHUNK_DATA_EMPTY            : EXPECT_CHUNK_CRLF;

        -- 4. Зачистка хвоста чанка
        state = EXPECT_CHUNK_CRLF & input = CRLF_VALID                : EXPECT_CHUNK_SIZE;
        state = EXPECT_CHUNK_CRLF & input = MALFORMED                 : ERROR;

        TRUE                                                          : ERROR;
    esac;
```

## 3. Математические Спецификации и Вердикт nuXmv
Для проверки живучести и безопасности системы в чекер были заложены следующие CTL/LTL формулы:

1. **Свойство Безопасности (Safety)**: Попав в терминальное состояние `SUCCESS`, автомат обязан остаться в нём навечно, блокируя любые рантайм-мутации.
   * `SPEC AG (state = SUCCESS -> AX (state = SUCCESS))` — **`is true`**
2. **Свойство Живучести (Liveness)**: При обнаружении чанкового режима автомат гарантированно переключается на фазу ожидания размера.
   * `SPEC AG (state = PARSE_HEADERS & input = HEADERS_PARSED_CHUNKED -> AX (state = EXPECT_CHUNK_SIZE))` — **`is true`**
3. **Свойство Цикличности (Cyclic Invariant)**: Из фазы зачистки хвоста при валидных байтах разделителя автомат совершает безупречное колебание обратно к чтению размеров.
   * `SPEC AG (state = EXPECT_CHUNK_CRLF & input = CRLF_VALID -> AX (state = EXPECT_CHUNK_SIZE))` — **`is true`**

## 4. Хроника ликвидации тупика
На этапе первичного тестирования спецификации чекер nuXmv выдал контрпример (*Counterexample*), обнаружив, что при достижении `SUCCESS` случайный входящий сигнал из среды перебрасывал автомат в дефолтную ветку `TRUE : ERROR;`. 
Проблема была устранена путём явного добавления инварианта `state = SUCCESS : SUCCESS;` в самый верх блока переходов. Система математически доказана на отсутствие дедлоков.
