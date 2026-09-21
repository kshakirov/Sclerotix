# Rigorous Engineering Methodology — Model, Proof, Conformance

Наша цель — не набрать побольше тестов, а получить **обоснованную уверенность в поведении программы**.

Принцип:

> **Model where valuable → prove model properties → derive discriminating traces → test implementation conformance → retain failures as regressions.**

## 1. Сначала модель

Если часть системы естественно является автоматом, сначала явно задаём:

\[
\delta : S \times I \rightarrow S'
\]

или, когда наблюдаем выход:

\[
S \times I \rightarrow O \times S
\]

где:

- \(S\) — состояние;
- \(I\) — вход;
- \(O\) — наблюдаемый выход;
- \(\delta\) — transition function.

Мы формализуем не всё приложение, а только тот фрагмент, где это оправдано сложностью и риском.

Это наш **MaxEnt**: не вводить больше формальной конструкции, чем требуется задачей.

## 2. Model Checking

Формальную модель проверяем с помощью **nuXmv** и temporal logic, прежде всего **LTL**.

Проверяем свойства вроде:

- **Safety** — плохое состояние недостижимо;
- **Reachability** — нужное состояние достижимо;
- **Liveness** — машина не застревает навечно там, где обязана продвигаться.

Если свойство нарушено, model checker даёт **counterexample trace** — конкретный путь машины к нарушению.

Важно:

> **Model checking доказывает свойства модели, а не автоматически свойства production-кода.**

Между ними остаётся **semantic gap**.

## 3. Model-Guided Conformance Testing

Модель становится источником осмысленных тестовых трасс.

Нас интересуют два класса:

```text
formal model
    │
    ├── valid / boundary traces
    │          ↓
    │    conformance tests
    │
    └── counterexample traces
               ↓
        regression tests
```

Мы проверяем, что реализация на той же последовательности входов демонстрирует поведение, согласованное с моделью.

Это **conformance testing**.

Для stateful-систем такой подход естественно связан с **model-based testing** и **stateful / model-guided PBT**.

Коалгебраическая интерпретация этой конструкции интересна нам как отдельная исследовательская линия, но не требуется для практического применения метода.

## 4. PBT и Fuzzing остаются

Формальная модель описывает только то, что мы в неё заложили.

Поэтому обычные:

- **Property-Based Testing**;
- **stateful PBT**;
- **fuzzing**

не заменяются model checking.

Они ищут проблемы за пределами наших текущих предположений.

Если такой тест находит новый класс ошибки, мы спрашиваем:

> должна ли эта ошибка стать свойством или ограничением формальной модели?

Так тестирование может уточнять модель, а модель — порождать более сильные тесты.

## 5. Correctness by Construction

Там, где язык позволяет, часть инвариантов переносим непосредственно в представление программы:

- algebraic data types;
- exhaustive pattern matching;
- **Type-State Pattern**;
- compile-time restrictions.

Идея проста:

> если невалидное состояние можно сделать непредставимым — лучше не проверять его в runtime.

Но система типов, model checking и тестирование решают разные задачи и не подменяют друг друга.

## 6. Runtime остаётся простым

Формальная строгость не должна превращать production runtime в верификатор.

В идеале ядро остаётся обычной дешёвой машиной:

\[
\delta(s,i) \rightarrow s'
\]

или

\[
\delta(s,i) \rightarrow (o,s')
\]

Без лишней аллокации, скрытого состояния и проверок, которые уже были устранены конструкцией.

**Proof machinery живёт вокруг машины, а не обязательно внутри неё.**

## Контур

```text
requirements / invariants
          ↓
     formal model
          ↓
     model checking
       ↙       ↘
valid traces   counterexamples
       \       /
        \     /
   conformance tests
          ↓
   implementation
          ↑
      PBT / fuzzing
```

Это не обещание «доказать всю программу».

Это инженерный цикл:

> **сформулировать → смоделировать → доказать доступное → прострелить реализацию → сохранить найденное → уточнить модель.**

Для Sclerotix естественные первые объекты этого метода — streaming parser automata и, по мере усложнения, readiness/event-loop state machine.