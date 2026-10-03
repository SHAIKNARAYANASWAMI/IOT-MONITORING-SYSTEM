# Efftronics Alignment

How this project maps to the Software Engineer requirements. Rule: claim only
what the project really contains. Where coverage is partial, this file says so.

---

## 1. C/C++
**Where:** `cpp_device/` (`sensor.h`, `sensor.cpp`, `main.cpp`, `test_sensor.cpp`). Struct, references, pointers with length, fixed arrays, bitwise alarm flags, `snprintf` with bounds, circular buffer with no heap, 12 assert tests.
**Learn:** pointer vs reference, const correctness, stack vs heap, bit operations (`|`, `&`, `~`, shifts), buffer overflow, RAII, `static_cast`, header vs source files.
**Likely question:** "Why are alarms stored as bit flags?"
**How to answer:** Six alarms fit in one byte, set with `|=`, tested with `&`. Compact for embedded memory and cheap to transmit. Example: `0x21` = HIGH_TEMP + LOW_BATTERY.
**Be honest:** it is a standalone PC program with simulated reads. It is not firmware, not on a microcontroller, and not linked to the Python backend.

## 2. Data structures
**Where:** `backend/app/core/`: ring buffer, moving average, binary min-heap priority queue. Also the bounded `queue.Queue` in ingestion and `dict` lookups.
**Learn:** array vs linked list, queue/stack, heap operations (sift up/down), hash map basics, time and space complexity of each.
**Likely question:** "How does your ring buffer work?"
**How to answer:** Fixed array plus start index and size. Append writes at `(start + size) % capacity`; when full it overwrites the oldest. O(1) insert, O(capacity) memory.

## 3. Algorithms
**Where:** merge sort (stable), `lower_bound`/`upper_bound` binary search, `range_query`, running-sum moving average, Kernighan bit count (C++), offline scan. Used by `analytics_service.py`.
**Learn:** Big-O, divide and conquer, stable vs unstable sorting, binary search boundaries, sliding window.
**Likely question:** "Why is your moving average O(1)?"
**How to answer:** Keep a running sum: add the new value, subtract the value that left the window. Recomputing the window each time would be O(window).
**Be honest:** the offline detector scan is O(n); a timeout min-heap is the improvement for 10,000 devices.

## 4. OOP / OOD
**Where:** `Rule` base class with subclasses (Strategy-like, Open/Closed), repositories (encapsulation), services (single responsibility), `MovingAverage` containing `RingBuffer` (composition), C++ classes.
**Learn:** four OOP pillars, SOLID, composition vs inheritance, Strategy and Repository patterns.
**Likely question:** "How would you add a new alert rule?"
**How to answer:** Add one `Rule` subclass and register it in `ALL_RULES`; the alert service does not change.
**Be honest:** I did not use abstract interfaces or fake repositories, so Liskov and Interface Segregation are only lightly applied.

## 5. Software architecture
**Where:** layers: MQTT, ingestion queue, validation, rules, services, repositories, API, dashboard. Folder structure mirrors the layers. Config from `.env`.
**Learn:** layered architecture, separation of concerns, producer-consumer, dependency injection, scaling and fault-tolerance basics.
**Likely question:** "Why a queue between subscriber and database?"
**How to answer:** The MQTT callback must return fast; a slow DB write must not block receiving. The bounded queue decouples them and limits memory.

## 6. Computer architecture
**Where:** only indirectly. Fixed-size buffers and no heap in C++ (memory constraints), `uint8_t` for compact data, bit-level flags, stack vs heap.
**Learn (study separately, not shown by this project):** CPU, registers, cache and memory hierarchy, endianness, how data types map to bytes, interrupts, stack frames, pipeline basics.
**Likely question:** "What is endianness?" or "Why does a struct have padding?"
**How to answer:** Say what you know (byte order, alignment makes memory access efficient). If unsure: "I have not built anything that depends on it, but I understand the concept as ..." Do not claim project experience here.

## 7. Operating systems
**Where:** threads (MQTT loop, ingestion worker, offline detector), thread-safe queue, daemon threads and clean shutdown, `threading.Event`, separate processes (API vs subscriber), Windows service conflict on port 1883.
**Learn:** process vs thread, GIL, race conditions, deadlock, mutex/semaphore, blocking vs non-blocking I/O, context switching, scheduling basics.
**Likely question:** "Is your code thread-safe?"
**How to answer:** Threads share only the thread-safe queue; each thread has its own DB session; counters are updated by one thread. Work is I/O-bound so the GIL is not a bottleneck.
**Be honest:** no locks were needed in this design, and I have not tested heavy concurrency.

## 8. Data communication
**Where:** MQTT publish/subscribe with QoS 1, topics and wildcards, reconnect with backoff, keepalive, HTTP REST with status codes, JSON message format, TCP ports 1883 and 8000.
**Learn:** TCP vs UDP, OSI/TCP-IP layers, HTTP methods and status codes, MQTT QoS 0/1/2, TLS basics, client-server vs pub/sub.
**Likely question:** "Why MQTT instead of HTTP for devices?"
**How to answer:** Lightweight, persistent connection, pub/sub decoupling, QoS levels, good for constrained devices and poor networks. HTTP suits request/response and browsers, so I also support `POST /telemetry`.
**Be honest:** the broker is local without TLS or authentication.

## 9. IoT
**Where:** device simulator (normal, fault, offline, low battery), telemetry format, thresholds, offline detection, alerts, dashboard monitoring.
**Learn:** sensor-gateway-cloud flow, MQTT in IoT, device provisioning, heartbeat/offline detection, edge vs cloud processing, device security.
**Likely question:** "How do you know a device is offline?"
**How to answer:** No message for 30 seconds. A background thread scans `last_seen` every 5 seconds, marks it OFFLINE and raises an alert; new data resolves it.
**Be honest:** all devices are simulated. No real hardware was used.

## 10. Testing
**Where:** about 80 pytest tests (unit and integration, API via `TestClient`), separate test database, 12 C++ assert tests.
**Learn:** unit vs integration, fixtures, test isolation, edge cases, mocking, test coverage, regression testing.
**Likely question:** "How do your tests avoid touching real data?"
**How to answer:** `conftest.py` sets `DATABASE_URL` to `test_iot.db` before importing the app and recreates the tables before every test.
**Be honest:** the live MQTT connection and dashboard JavaScript are tested manually only.

## 11. Debugging
**Where:** structured logging, following the pipeline hop by hop, real bugs fixed: duplicate alerts, Ctrl+C on Windows, test file not discovered, port already in use, wrong shell for venv.
**Learn:** reading stack traces, logging levels, reproducing a bug, isolating by layer, using a debugger (breakpoints), `git log`/`git diff` to find regressions.
**Likely question:** "The dashboard shows no data. What do you check?"
**How to answer:** Work backwards: browser network tab, `/devices` response, subscriber logs, broker PUBLISH logs, simulator. Check logs at each hop.
**Tip:** practise using the VS Code debugger with a breakpoint in `process()`, since the interviewer may ask about it.

## 12. Communication skills
**Where:** README, this document, INTERVIEW_PREPARATION.md, clear commit history, the 60-second and 3-minute pitches.
**Learn:** explain in layers (one sentence, then detail), state trade-offs and limits, say "I do not know, but here is how I would find out", ask clarifying questions.
**Likely question:** "Explain your project to a non-technical person."
**How to answer:** "Many machines have sensors. My software collects their readings, shows them on one screen, and warns the operator when something looks wrong, like overheating or a machine going silent."
**Practice:** say the 60-second pitch aloud, time it, and record yourself once.

---

## Things NOT to claim
- Real hardware, firmware or microcontroller experience.
- Production scale, load testing, or cloud deployment.
- Docker, Kubernetes, Kafka, Redis, TLS, or PostgreSQL (not used here).
- That the C++ module is connected to the Python backend.
- Work you cannot explain line by line.
