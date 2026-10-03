# IoT Device Monitoring and Alert System

A small industrial-IoT style monitoring product: simulated devices publish sensor
readings over MQTT, a Python backend validates and stores them, a rule engine
raises alerts, and a web dashboard shows live status.

> **Honest scope:** devices are **simulated in software**. No real hardware was
> used. The C++ module is a **standalone PC program** that mirrors firmware-style
> logic. It does not run on a microcontroller and is not connected to the backend.

## Problem statement
Plants and facilities have many devices (sensors, meters). Operators need to see
device health in real time and be warned quickly when something is abnormal
(overheating, low battery, voltage problems) or when a device goes silent.

## Objectives
- Receive telemetry from many devices (MQTT and HTTP).
- Validate data before it reaches the database.
- Detect abnormal conditions and generate alerts, without duplicates.
- Detect offline devices.
- Show live status, history charts and alerts on a dashboard.
- Keep the code layered, testable and explainable.

## Features
- MQTT ingestion with automatic reconnect, plus `POST /telemetry` over HTTP
- Validation (range checks, NaN rejected, device-id format)
- Producer-consumer ingestion (bounded queue and worker thread)
- Configurable rule engine (thresholds per metric, global or per device)
- Alert lifecycle: OPEN, ACKNOWLEDGED, RESOLVED, with auto-resolve
- Offline detection (no data for 30 seconds by default)
- REST API with JWT-protected write endpoints
- Dashboard: summary cards, device table, 4 charts, alert actions
- Own DSA code: ring buffer, moving average, min-heap priority queue,
  merge sort, binary search
- 75+ automated Python tests and 12 C++ tests

## Architecture

```
Device Simulator --MQTT--> Mosquitto Broker --> MQTT Subscriber
                                                     |
                                              Ingestion queue
                                                     |
                                       Validation (Pydantic schema)
                                                     |
                                  Repository --> SQLite (SQLAlchemy)
                                                     |
                                   Alert Service + Rule Engine
                                                     |
 Offline Detector (background thread) ---------------+
                                                     |
                  REST API (FastAPI) <--> Dashboard (HTML/CSS/JS, Chart.js)
```

| Layer | Folder | Purpose |
|---|---|---|
| Communication | `backend/app/mqtt` | Receive messages, reconnect |
| Ingestion | `backend/app/services/ingestion_service.py` | Queue and worker thread |
| Validation | `backend/app/schemas` | Reject bad data early |
| Rules | `backend/app/rules` | One class per metric rule |
| Services | `backend/app/services` | Alert, offline, analytics logic |
| Repositories | `backend/app/repositories` | Only code that touches the DB |
| API | `backend/app/api` | Thin HTTP layer |
| DSA | `backend/app/core` | Ring buffer, heap, sorting, search |
| Dashboard | `frontend` | Live UI, polls API every 3 s |
| Device logic (C++) | `cpp_device` | Firmware-style prototype |

## Technology stack
Python 3.10, FastAPI, SQLAlchemy 2, SQLite, Pydantic, paho-mqtt, PyJWT, pytest,
Mosquitto, HTML/CSS/JavaScript, Chart.js, C++17 (g++).

## System workflow
1. A device (simulator) publishes JSON to `iot/devices/{device_id}/telemetry`.
2. The subscriber receives it and puts it in a bounded queue.
3. A worker thread validates it, saves the reading, updates `last_seen`.
4. The alert service evaluates every rule and creates alerts (no duplicates).
5. Normal values auto-resolve alerts; fresh data resolves `DEVICE_OFFLINE`.
6. The offline detector marks silent devices OFFLINE and raises an alert.
7. The dashboard polls the REST API and redraws.

## Database schema
| Table | Purpose |
|---|---|
| `devices` | device_id (unique), name, location, status, last_seen |
| `sensor_readings` | readings per device, index on (device_id, timestamp) |
| `thresholds` | min/max/severity per metric, global or per device |
| `alerts` | type, severity, actual/threshold value, status, timestamps |
| `system_logs` | table exists; runtime logging currently goes to the console |

`alerts` has CHECK constraints on severity and status.

## API (summary)
| Method | URL | Auth |
|---|---|---|
| GET | `/health` | no |
| POST | `/auth/login` | no |
| POST / GET | `/devices` | POST needs token |
| GET | `/devices/{id}`, `/devices/{id}/readings?limit=` | no |
| POST | `/telemetry` | no |
| GET | `/alerts?status=` | no |
| PUT | `/alerts/{id}/acknowledge`, `/alerts/{id}/resolve` | token |
| POST / GET | `/thresholds` | POST needs token |
| GET | `/analytics/urgent-alerts`, `/analytics/alert-report`, `/analytics/devices/{id}/smoothed-temperature` | no |

Interactive docs: `http://127.0.0.1:8000/docs`. Typical errors: 401 missing or
bad token, 404 not found, 409 duplicate device, 422 validation error.

## Installation (Windows)
1. Install Python 3.10+, Git, VS Code, and Mosquitto.
2. Create and activate a virtual environment:
```
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
3. Copy `.env.example` to `.env` and set your own secrets.
4. Create the database and default thresholds:
```
python -m scripts.init_db
python -m scripts.seed_thresholds
```

## Configuration
All settings come from `.env` (see `.env.example`): database URL, MQTT host and
port, offline timeout, JWT secret and expiry, admin credentials, log level.
`.env` is git-ignored.

## How to run (4 terminals)
| Terminal | Command |
|---|---|
| 1 Broker | `mosquitto -c mosquitto.conf -v` |
| 2 API | `python -m uvicorn backend.app.main:app --reload` |
| 3 Subscriber | `python -m backend.app.mqtt.subscriber` |
| 4 Simulator | `python -m device_simulator.simulator --devices 5 --interval 2 --fault-chance 0.15` |

Open `http://127.0.0.1:8000/`. Write actions (Acknowledge/Resolve) ask for the
admin login.

## How to test
```
python -m pytest -v
```
C++ tests:
```
cd cpp_device
g++ -std=c++17 -Wall -Wextra -o test_sensor.exe test_sensor.cpp sensor.cpp
.\test_sensor.exe
```

## Screenshots
_Add screenshots here: dashboard overview, alerts table, /docs page._

## Known limitations and future improvements
- SQLite is fine for a demo; use PostgreSQL or TimescaleDB for scale.
- Dashboard polls; WebSockets or Server-Sent Events would push updates.
- MQTT runs without TLS or authentication in local mode; add both for real use.
- The offline detector scans all devices (O(n)); a timeout min-heap would scale better.
- Admin credentials come from `.env`; a real system needs a user table with hashed passwords.
- Subscriber and API are separate processes sharing one DB file; use a server database for multi-node.

## Learning outcomes
Layered architecture, producer-consumer threading, MQTT pub/sub, REST design
with proper status codes, JWT basics, relational design, rule engines (Strategy
pattern), implementing core data structures, testing with a separate database,
and C++ bitwise and fixed-memory techniques.
