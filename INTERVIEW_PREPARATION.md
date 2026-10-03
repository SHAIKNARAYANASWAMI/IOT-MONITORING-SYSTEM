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
