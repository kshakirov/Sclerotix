# Issue #3 — Баг по поводу автомата в nuXmv есть циклы


**State:** OPEN
**Author:** @kshakirov
**Created:** 2026-08-10T07:38:35Z
**Updated:** 2026-08-10T08:08:10Z
**URL:** https://github.com/kshakirov/Sclerotix/issues/3

---

# Bug Report: LTL Specification Violation / Loop Detection on Head Empty Signals

## Status
* **Ticket ID**: #005
* **Component**: `http_parse_automaton` (Core Model Verification)
* **Severity**: Major (Potential DoS / Execution Loop)
* **Branch**: `dev-buffer`

## Problem Description
Formal verification via `nuXmv` detected a CTL/LTL counterexample for the liveness specification:
`SPEC AG (state = PARSE_HEADERS -> AF (state = SUCCESS | state = ERROR))`

When the stream runs out of bytes during the initial parsing phases, the physical shell yields a `CHUNK_DATA_EMPTY` signal. Under pure mathematical model parameters, this forces a transition loop (`PARSE_HEADERS` -> `CHUNK_DATA_EMPTY` -> `PARSE_HEADERS`), causing the verification runner to fail the bounded liveness constraint (`AF`).

In live environments, this mapping translates directly to thread starvation or infinite looping states if a client stops sending payload middle-stream (Slowloris attack vector).

## Root Cause Analysis
1. **DFA Traps**: The pure shutter lacks an upper-bounded iteration register to force an exit loop if starvation occurs.
2. **Asymmetry Between Model and Network**: In practice, a network timeout must intervene, which was absent from the strict Type-3 Chomsky state transition projection.

## Proposed Strategy / Constraints for Fix
* Implement a low-level starvation index counter inside the Reynolds ADT shell (`run_engine` closure).
* Map loop limits to a concrete `TIMEOUT` token transition to drop into `State.ERROR` gracefully.
* Maintain zero-heap allocation principles.

---
*Generated snapshot for future session reload.*


---

## Comments

