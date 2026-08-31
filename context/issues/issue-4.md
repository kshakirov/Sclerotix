# Issue #4 — Создание и Изоляция арены для конкретного пользователя


**State:** OPEN
**Author:** @kshakirov
**Created:** 2026-08-10T08:07:18Z
**Updated:** 2026-08-20T07:00:40Z
**URL:** https://github.com/kshakirov/Sclerotix/issues/4

---

# Ticket: Implement Session Registry and Ephemeral Arena Mapping

## Status
* **Ticket ID**: #006
* **Component**: `network_layer` / `event_loop`
* **Severity**: Critical (Architectural Foundation)
* **Milestone**: Milestone 2 (POSIX Sockets Integration & Connection Mapping)

## Objective
Implement a centralized, zero-leak session registry that binds incoming POSIX socket data fragments to independent, isolated Arena environments based on the transport endpoint tuple.

## Specification & Technical Constraints
1. **Endpoint Resolution**: Retrieve the unique `(ip, port)` matrix immediately upon `socket.accept()` or read invocation.
2. **Context Lifespan**:
   * **On Connect/First Read**: If `(ip, port)` is not present in the registry, instantiate a fresh Arena context (`bytearray`) and initialize pointers (`buffer_pointer = 0`).
   * **On Fragment Read**: Fetch the existing session state from the registry, execute `.extend()` on the active Arena buffer, and resume parsing exactly from the last saved `buffer_pointer`.
   * **On State Terminate (`SUCCESS` / `ERROR`)**: Evict the `(ip, port)` key from the registry immediately to prevent dangling memory anchors and memory leaks.
3. **No High-Level Abstractions**: The registry must operate on primitive dictionaries and integers. No object-relational mapping or heavy memory footprints allowed.


**Ticket #006: Integration of Zero-Allocation Arena Allocator into Operating Shell (Automaton 2)**

**Status:** Open / In Progress

**Priority:** High

**Module:** `lib/parsing/http_parse_automaton.py` / Transport Layer

**Target Architecture:** Reynolds ADT Closure & Zero-Allocation Buffer (ADR 0008)

---

**1. Context & Architectural Goal**
To preserve zero-heap-allocation behavior across persistent Keep-Alive connections, payload extraction must avoid slicing operations (`buffer[start:end]`). All incoming payload bytes must be direct-written to a single session-bound, contiguous `bytearray` (Arena).

---

**2. Scope of Work**

* **Signature Alignment:** Pass `arena: bytearray` into payload extractor routines (`read_chunk_variable_length`, `read_chunk_fixed_length`) and the main dispatcher (`run_engine`).
* **Byte Accumulation:**
* In streaming/1-byte torture test mode: append byte-by-byte (`arena.append(buffer[buffer_pointer])`).
* In block reads: append via `arena.extend(...)` when chunk boundaries allow.


* **Lifecycle Management:**
* Ensure clear decoupling between transport read-buffer pointer shifts and Arena appends.
* Execute `arena.clear()` upon reaching `State.SUCCESS` to recycle memory without GC overhead.



---

**3. Verification Criteria**

* **1-Byte Torture Test Pass:** Zero byte loss or state misalignment when parsing `FRAGMENTED_STREAM` character-by-character into `arena`.
* **Payload Integrity Check:** Assert `bytes(arena) == expected_payload` upon reaching `State.SUCCESS`.
* **Zero Allocation Guard:** No string or byte slicing created inside payload extraction loops.

---

Готово, брат. Тикет оформил строго по канону архитектуры Sclerotix. Забирай в работу, жду обновленный код на проверку!

---

## Comments


### @kshakirov — 2026-08-11T08:27:16Z

Остановился на новом правиле для перехода из  expect chunk size to expect chunk crlf а оттуда если есть данные  то с сигналом  to REad -data flow

---
