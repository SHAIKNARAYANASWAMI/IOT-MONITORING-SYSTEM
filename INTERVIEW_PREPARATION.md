# Interview Preparation: IoT Device Monitoring and Alert System

Rule: say only what you built and can explain. If you do not know, say
"I have not worked with that, but here is how I would approach it."

---

## Pitches

### Explain your project in 60 seconds
I built an IoT device monitoring system. Simulated devices publish temperature,
voltage, current and battery readings over MQTT. A Python backend receives them,
validates them, stores them in a database and runs a rule engine that raises
alerts, for example high temperature or low battery. A background thread detects
devices that stop sending data. A FastAPI REST API exposes everything and a web
dashboard shows live status, charts and alerts. I also wrote core data
structures myself (ring buffer, min-heap, merge sort, binary search), a C++
module for device-side logic with bitwise alarm flags, and about 80 automated
tests. The devices are simulated, not real hardware.

### Explain your project in 3 minutes
Problem: operators of many devices need live health status and quick warnings.

Flow: a simulated device publishes JSON to the MQTT topic
`iot/devices/{id}/telemetry`. My subscriber receives the message and puts it in
a bounded queue so the network thread never waits for the database. A worker
thread takes messages from the queue, validates them with a Pydantic schema
(range checks, NaN rejected), saves the reading and updates `last_seen`. Then the
alert service runs one rule class per metric against thresholds stored in the
database. It creates an alert only if no active alert of that type exists, and
auto-resolves it when the value returns to normal. A separate offline detector
thread checks every 5 seconds for devices silent longer than 30 seconds.

API and UI: FastAPI exposes devices, readings, alerts and thresholds. Write
endpoints need a JWT. The dashboard polls the API every 3 seconds and shows
cards, a device table, four charts and an alerts table with Acknowledge.

Engineering: layered code (API, services, repositories, models), repositories
are the only code touching the database, tests use a separate test database,
and I implemented ring buffer, moving average, priority queue, merge sort and
binary search myself and used them in an analytics service. The C++ module is a
standalone PC program that shows struct, pointers, bit flags and fixed-size
buffers. It is not on a microcontroller.

Limits: SQLite, polling, no TLS on MQTT, single admin account from `.env`.

### Explain your personal contribution
EDIT THIS to match what you really did. Suggested honest version: "I built the
project step by step. I wrote and can explain the layers: MQTT ingestion, queue
and worker, validation, rule engine, alert lifecycle, REST API with JWT, the
dashboard, the DSA code, tests and the C++ module. I used documentation and an
AI assistant for guidance and debugging, and I ran and tested every part
myself." Never claim a part you cannot explain.

### Biggest technical challenge
Pick one real one and know it deeply. Good real examples from this project:
1. Duplicate alerts: every reading above the limit created a new alert. Fix:
   check for an active alert of the same type first, and auto-resolve on normal.
2. Ctrl+C not stopping the subscriber on Windows when the main thread blocked
   on one endless wait. Fix: loop with short sleeps and stop threads cleanly.
3. Timestamps: devices send UTC with timezone, the database stores naive UTC,
   the browser needs to know it is UTC. Fix: convert once in validation and add
   Z in JavaScript.

---

## A. Project architecture

**Q1. Walk me through the architecture.**
Device to MQTT broker to subscriber to bounded queue to worker (validate, save,
rules) to SQLite. FastAPI reads the same database and the dashboard polls the
API. Each layer has one job so I can test and change it independently.

**Q2. Why a queue between the subscriber and the database?**
The MQTT callback must return fast. A slow database write would block message
receiving. The queue decouples producer and consumer (producer-consumer
pattern). It is bounded (1000) so memory cannot grow without limit.
Follow-up: what if it is full? I drop the message, log an error and count it in
`dropped`. Trade-off: we lose data under overload. A real system could use a
persistent broker queue or backpressure.

**Q3. Why validate before saving?**
Sensors send garbage (9999, NaN, missing fields). Rejecting early keeps the
database clean and stops false alerts. Pydantic enforces ranges and types.

**Q4. How do you avoid alert storms?**
One active alert per (device, alert type). `find_active` checks before creating.
When the metric is normal again the alert auto-resolves. Follow-up: what if the
value flaps around the limit? It would create and resolve repeatedly. A fix is
hysteresis (resolve only after the value is a margin below the limit).

**Q5. Why a repository layer?**
Only repositories touch SQLAlchemy. Services stay free of SQL, so I can change
the database or test services more easily (dependency inversion idea). Honest
note: my tests use a real test database, not fake repositories.

**Q6. What are the weak points of your design?**
SQLite and a polling dashboard do not scale. No TLS or MQTT auth in local mode.
`POST /telemetry` has no authentication. A single admin from `.env`. The
subscriber and API are separate processes sharing one DB file. I would list
these as future work, not hide them.

---

## B. Python

**Q7. How do you use threads and what about the GIL?**
I run the MQTT network loop, the ingestion worker and the offline detector in
threads. The GIL lets only one thread run Python bytecode at a time, but my
work is mostly I/O (network, database), where threads release the GIL while
waiting, so threads are fine. For CPU-heavy work I would use multiprocessing.

**Q8. Is your code thread-safe?**
Shared state between threads is the `queue.Queue` (thread-safe) and counters
(`processed`, `rejected`) that only the worker updates. Each thread opens its
own database session. SQLite needs `check_same_thread=False` because several
threads use connections. Honest note: the counters are read from another
thread without a lock, which is fine for display only.

**Q9. What is `Depends(get_db)` in FastAPI?**
Dependency injection. `get_db` is a generator: it yields a session to the
endpoint and the `finally` block closes it afterwards, even on errors. It also
makes testing easier because the dependency can be replaced.

**Q10. Why Pydantic?**
Declarative validation and parsing. Wrong types or out-of-range values raise
`ValidationError`, and FastAPI turns that into HTTP 422 automatically. It also
generates the OpenAPI docs at `/docs`.

**Q11. What does `@lru_cache` do on `get_settings`?**
It caches the return value, so `.env` is read once and every caller gets the
same Settings object (a simple singleton).

**Q12. Why `hmac.compare_digest` for the password check?**
It compares in constant time, which avoids timing attacks where an attacker
measures how long a comparison takes to guess a secret character by character.

---

## C. C/C++

**Q13. Explain your C++ module.**
It is a standalone PC program that mimics firmware-style logic: a `SensorData` struct, `validateSensorData`, `checkThreshold`, `calculateAverage`, `generateAlert`, and a fixed-size circular buffer. Sensor reads are random numbers, not real hardware. It is not on a microcontroller and not connected to the Python backend.

**Q14. Why use bit flags for alarms?**
Six alarms fit in one byte (`uint8_t`), one bit each. Set with `|=`, test with `&`, clear with `&= ~flag`. Compact for embedded memory and cheap to send over a network. Example: `0x21` = HIGH_TEMP (bit 0) + LOW_BATTERY (bit 5).

**Q15. Pointer vs reference?**
A reference is an alias that cannot be null and cannot be reseated. A pointer can be null and can change. I use `SensorData&` when the function must fill a caller's struct, and `const float*` plus a length in `calculateAverage` like a C array, with a null check.
Follow-up: why `const`? It promises the function will not modify the data and lets the compiler catch mistakes.

**Q16. Why no `new`/`malloc` in the circular buffer?**
Embedded systems have little memory and heap fragmentation is a risk. A fixed array has predictable memory and no allocation failure at runtime.

**Q17. How do you avoid buffer overflow in `generateAlert`?**
`snprintf` with the remaining size, and I stop if the next write would not fit. A test uses a tiny 8-byte buffer to check the string stays terminated.

**Q18. Stack vs heap?**
Stack: automatic, fast, freed on function exit, limited size. Heap: manual or RAII-managed, flexible lifetime, slower, can fragment or leak. My C++ module uses only the stack.

**Q19. What does `static_cast` do and why use it?**
Explicit, checked-at-compile-time type conversion. Clearer and safer than a C-style cast because it states intent and is easy to search for.

**Q20. How does Kernighan's bit count work?**
`n &= (n - 1)` clears the lowest set bit, so the loop runs once per set bit, not once per bit position.

---

## D. OOP

**Q21. Where did you use OOP and which principles?**
Rule classes inherit from a `Rule` base class and override `metric` and alert names (Strategy-like, Open/Closed: add a new rule without editing the engine). Repositories encapsulate DB access. Services have a single responsibility each.

**Q22. Explain SOLID with your project.**
S: each service/repository has one job. O: new rule = new class. D (partly): services use repositories instead of raw SQL. Honest note: I did not implement full interfaces/abstract classes or fake repositories, so Liskov and Interface Segregation are only lightly applied.

**Q23. Inheritance vs composition?**
Rules use inheritance for shared evaluate logic. `MovingAverage` uses composition: it contains a `RingBuffer` rather than extending it, because it is not a kind of ring buffer.

**Q24. What is encapsulation in `RingBuffer`?**
Internal array, start index and size are underscore-private. Callers use `append`, `to_list`, `latest`, `oldest`, so the wrap-around logic cannot be broken from outside.

---

## E. Data structures

**Q25. Which data structures did you implement yourself?**
Ring buffer, moving average (on the ring buffer), binary min-heap priority queue, merge sort and binary search (lower/upper bound). They are used in the analytics service and tested.

**Q26. Ring buffer: how does it work?**
Fixed array, a start index and a size. Append writes at `(start + size) % capacity`. When full it overwrites the oldest and advances start. Insert O(1), memory O(capacity).

**Q27. Why a heap for alerts?**
Push and pop are O(log n) and the most urgent is always at the top. A tie counter keeps same-severity alerts FIFO. Honest note: in `urgent_alerts` I push everything then pop `count` items, so it is O(n log n); a sort would also work. The heap shines when alerts arrive continuously.

**Q28. Where do you use a hash map?**
Python `dict` for severity ranking and the database unique index on `device_id` for lookup. Average O(1) lookup; collisions are handled internally by Python (open addressing).

**Q29. Queue vs stack?**
Queue is FIFO (my ingestion queue), stack is LIFO. Messages must be processed in arrival order, so a queue.

---

## F. Algorithms

**Q30. Merge sort complexity and why stable?**
Time O(n log n) always, extra space O(n). Using `<=` when merging keeps equal items in original order. I rely on stability: sort by time first, then by severity, so newest-first holds inside each severity.

**Q31. Binary search: what is lower_bound?**
Index of the first item with key >= target, in O(log n). Combined with upper_bound it gives a range query in O(log n + k).
Follow-up: precondition? The list must be sorted by that key.

**Q32. Moving average complexity?**
O(1) per reading using a running sum: add the new value, subtract the one that left the window. Recomputing the window each time would be O(window).

**Q33. Offline detection complexity?**
Each scan is O(n) over devices. At 10,000 devices I would use a min-heap keyed by expiry time so only the earliest-expiring device is checked, O(log n) per update.

**Q34. Why implement merge sort when Python has `sorted`?**
To show I understand the algorithm and its trade-offs. In production I would use the built-in (Timsort), which is faster and well tested.

---

## G. MQTT

**Q35. Why MQTT instead of HTTP for devices?**
Lightweight headers, persistent connection, publish/subscribe (devices do not need to know the consumers), QoS levels, and low bandwidth, good for constrained devices and bad networks. HTTP is request/response and heavier per message.
Follow-up: where is HTTP better? Simple request/response APIs, browsers, easy debugging. That is why my REST API also accepts `POST /telemetry`.

**Q36. Explain pub/sub and the broker.**
Publishers send to a topic, the broker routes to subscribers of that topic. They never connect directly. My topic: `iot/devices/{id}/telemetry`; the backend subscribes to `iot/devices/+/telemetry` (`+` = one-level wildcard).

**Q37. What QoS do you use?**
QoS 1 (at least once): the broker acknowledges with PUBACK, so duplicates are possible. Honest note: with duplicates a reading could be stored twice; I did not add de-duplication. QoS 0 is fire-and-forget, QoS 2 is exactly-once but slower.

**Q38. How does reconnection work?**
paho's `reconnect_delay_set` retries with backoff. I subscribe inside `on_connect`, so subscriptions are restored after every reconnect. I tested it by stopping the broker and watching the subscriber reconnect.

**Q39. What is keepalive?**
The client sends PINGREQ if idle so the broker knows it is alive. Visible in the broker logs as PINGREQ/PINGRESP.

**Q40. Security gaps in my MQTT setup?**
Local broker with anonymous access and no TLS. For real use: username/password or client certificates, TLS on port 8883, and topic ACLs so a device can publish only to its own topic.

---

## H. Networking

**Q41. TCP vs UDP?**
TCP: connection-oriented, reliable, ordered, with flow and congestion control. UDP: connectionless, no guarantees, lower overhead. MQTT and HTTP run on TCP.

**Q42. What happens when you open the dashboard URL?**
DNS/IP (here localhost), TCP handshake to port 8000, HTTP GET `/`, FastAPI returns the HTML, then the browser fetches JS/CSS and the JS calls the API with `fetch`.

**Q43. What are ports 1883 and 8000?**
1883 is the default MQTT port (8883 for TLS). 8000 is where uvicorn serves the API. Each listens on a TCP socket.

**Q44. Client-server vs pub/sub?**
Client-server: client asks a specific server and waits for a reply (REST). Pub/sub: producers and consumers are decoupled through a broker, and communication is event-driven.

---

## I. REST APIs

**Q45. Which status codes do you use and when?**
200 OK (read/update), 201 Created (new device, telemetry stored), 401 Unauthorized (missing/bad token), 404 Not Found (unknown device or alert), 409 Conflict (duplicate device), 422 Unprocessable Entity (validation error).

**Q46. PUT vs POST?**
POST creates or triggers an action and is not idempotent. PUT replaces/updates a known resource and should be idempotent. Honest note: my acknowledge/resolve are PUT on action URLs; calling them twice gives the same final state, so they are idempotent in effect.

**Q47. How does your JWT auth work?**
`POST /auth/login` checks credentials from `.env` and returns a signed token (HS256) with an expiry. Write endpoints use `Depends(require_auth)`, which decodes and verifies the token, else 401. Limits: single admin, password in `.env`, no refresh tokens, and `POST /telemetry` is unauthenticated. A real system needs hashed passwords in a user table and per-device credentials.

**Q48. Why are GET endpoints open?**
Simplicity for the demo dashboard. In production I would protect reads too.

---

## J. Database

**Q49. Explain your schema and relationships.**
`devices` (unique `device_id`) has many `sensor_readings` and `alerts` through foreign keys. `thresholds` has a nullable `device_id`: NULL means a global default, a value means a per-device override. `alerts` has CHECK constraints on severity and status.

**Q50. Why index (device_id, timestamp)?**
The main query is "latest N readings for one device, newest first". The composite index lets the database find the device's rows and read them in time order without scanning the table.

**Q51. How do you reduce DB load?**
Limit queries (`limit`), index the hot paths, batch inserts, downsample or aggregate old readings, delete old data with a retention policy, cache latest values, and move to PostgreSQL or a time-series database.
Honest note: my dashboard currently makes one latest-reading call per device every 3 seconds, which is an N+1 pattern. A single "latest per device" endpoint would fix it.

**Q52. What is an upsert and why was it needed?**
Update if exists, else insert. For thresholds, `UNIQUE(device_id, metric)` does not stop duplicates when `device_id` is NULL in SQLite (NULLs are distinct), so I check in code first.

**Q53. What is a transaction?**
A group of operations that succeed or fail together (ACID). Each repository method commits after its change. Honest note: one reading plus its alerts are separate commits, so a crash between them could leave a reading without its alert check.

---

## K. Operating systems

**Q54. Process vs thread?**
A process has its own memory space; threads share a process's memory. My subscriber is one process with several threads; the API is a separate process.

**Q55. Which concurrency issues can happen?**
Race conditions, deadlocks, and starvation. I avoid shared mutable state by passing messages through a thread-safe queue and giving each thread its own DB session.

**Q56. What is blocking vs non-blocking?**
The MQTT callback must not block, so it only enqueues (`put_nowait`). The worker may block on the DB. Blocking the network thread would delay or lose messages.

**Q57. What happens when the queue is full?**
`put_nowait` raises `queue.Full`; I drop the message, log it, and count it. It is a deliberate load-shedding choice.

**Q58. How do daemon threads and shutdown work?**
Worker threads are daemon threads, so they will not keep the process alive. On Ctrl+C I stop the MQTT client, set a stop event, and join the threads for a clean exit.

---

## L. Testing

**Q59. What did you test?**
Unit tests: rules, validation, ring buffer, moving average, heap, sort/search. Integration tests: repositories, alert lifecycle, offline detector, ingestion pipeline, and the API with `TestClient` (status codes, auth). About 80 Python tests and 12 C++ `assert` tests.

**Q60. How do tests avoid touching real data?**
`conftest.py` sets `DATABASE_URL` to a separate `test_iot.db` before the app is imported and recreates tables before each test.

**Q61. Unit vs integration test?**
Unit: one piece in isolation (a rule). Integration: several pieces together (HTTP, service, database).

**Q62. What is not tested?**
The live MQTT connection, the dashboard JavaScript, and concurrency under load. The MQTT path was tested manually with the broker. I would add an MQTT integration test and load tests.

---

## M. Debugging

**Q63. How would you debug "the dashboard shows no data"?**
Follow the pipeline backwards. Is the browser calling the API (F12 Network)? Does `/devices` return data? Is the subscriber running and logging "Received"? Is the broker receiving PUBLISH (`mosquitto -v`)? Is the simulator running? Check logs at each hop.

**Q64. Real bugs you hit?**
Duplicate alerts, Ctrl+C not stopping on Windows, a venv not activated in the right shell, port 1883 already used by the Mosquitto Windows service, and test files not discovered because of a wrong name.

**Q65. How do you use logging?**
Python `logging` with timestamp, level, component and message. INFO for normal events, WARNING for alerts and offline devices, ERROR for failures, `logger.exception` to capture stack traces.

---

## N. Software architecture

**Q66. How would you scale to 10,000 devices?**
Ingestion: multiple subscriber instances using MQTT shared subscriptions, or a clustered broker (EMQX/HiveMQ). Storage: PostgreSQL with partitioning or TimescaleDB, batch inserts. Processing: a message queue (Kafka/RabbitMQ) between ingestion and rules, stateless workers. Cache latest state in Redis. Dashboard: WebSockets or SSE, aggregate endpoints. Offline detection: timeout min-heap. Say clearly that I have not built or load-tested this.

**Q67. How would you make it fault tolerant?**
Broker cluster, persistent sessions and QoS 1, retry with backoff, durable queue instead of in-memory, database replication and backups, health checks with auto-restart, idempotent processing to handle duplicates.

**Q68. How would you secure device communication?**
TLS on MQTT, per-device credentials or client certificates, topic ACLs, validate payload size and fields, rate limiting, signed firmware and rotating secrets, and authenticate `POST /telemetry` with device API keys.

**Q69. What would you change if you started again?**
Fake repositories for faster unit tests, a DB log handler, hysteresis on alerts, one aggregated "latest readings" endpoint, authentication for telemetry, and Docker Compose for one-command startup.

**Q70. Why layered architecture?**
Separation of concerns: each layer can be understood, tested, and replaced on its own. API code stays thin and business rules live in services.
