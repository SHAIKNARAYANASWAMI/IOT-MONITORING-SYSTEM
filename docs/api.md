# API Documentation

Base URL: `http://127.0.0.1:8000`. Interactive docs: `/docs`.
Protected endpoints need the header `Authorization: Bearer <token>`.

## Authentication

### POST /auth/login
Request:
```json
{"username": "admin", "password": "admin123"}
```
Response 200:
```json
{"access_token": "<jwt>", "token_type": "bearer"}
```
Errors: 401 `{"detail": "Invalid credentials"}`

## Health

### GET /health
Response 200:
```json
{"status": "ok", "database": "connected", "devices_total": 5, "devices_online": 3, "active_alerts": 4}
```

## Devices

### POST /devices (token required)
Request:
```json
{"device_id": "DEVICE-010", "name": "Boiler sensor", "location": "Plant A"}
```
Response 201:
```json
{"device_id": "DEVICE-010", "name": "Boiler sensor", "location": "Plant A", "status": "OFFLINE", "last_seen": null, "created_at": "2026-10-03T10:00:00"}
```
Errors: 401 missing or bad token, 409 `Device DEVICE-010 already exists`, 422 invalid device_id.

### GET /devices
Response 200: list of devices (same shape as above).

### GET /devices/{device_id}
Response 200: one device. Errors: 404 `Device NOPE not found`.

### GET /devices/{device_id}/readings?limit=100
`limit` 1 to 1000, newest first.
Response 200:
```json
[{"device_id": "DEVICE-001", "timestamp": "2026-10-03T10:00:00", "temperature": 35.5, "humidity": 60.0, "voltage": 230.0, "current": 4.2, "pressure": 101.3, "battery": 87}]
```
Errors: 404 unknown device.

## Telemetry

### POST /telemetry
Request:
```json
{"device_id": "DEVICE-010", "temperature": 35.5, "humidity": 60, "voltage": 230, "current": 4.2, "pressure": 101.3, "battery": 87}
```
Response 201:
```json
{"status": "stored", "device_id": "DEVICE-010"}
```
Errors: 422 `Invalid temperature: Input should be less than or equal to 150`.
Note: unauthenticated in this demo.

## Alerts

### GET /alerts?status=OPEN&limit=100
`status` is one of OPEN, ACKNOWLEDGED, RESOLVED (optional).
Response 200:
```json
[{"id": 11, "device_id": "DEVICE-002", "alert_type": "LOW_VOLTAGE", "severity": "CRITICAL", "actual_value": 155.9, "threshold_value": 200.0, "status": "OPEN", "created_at": "2026-10-03T10:00:00", "acknowledged_at": null, "resolved_at": null}]
```
Errors: 422 invalid status.

### PUT /alerts/{id}/acknowledge (token required)
Moves OPEN to ACKNOWLEDGED. A RESOLVED alert is returned unchanged.
Errors: 401, 404 `Alert 9999 not found`.

### PUT /alerts/{id}/resolve (token required)
Moves the alert to RESOLVED. Errors: 401, 404.

## Thresholds

### POST /thresholds (token required)
Request:
```json
{"metric": "temperature", "min_value": 5, "max_value": 60, "severity": "CRITICAL", "device_id": null}
```
`metric`: temperature, humidity, voltage, current, pressure, battery. `device_id` null means global.
Response 200: the saved threshold with its `id`.
Errors: 401, 404 unknown device, 422 (`min_value must be less than max_value`, or neither limit given, or unknown metric).

### GET /thresholds
Response 200: list of thresholds.

## Analytics

### GET /analytics/urgent-alerts?count=10
Active alerts, most severe first (own min-heap).

### GET /analytics/alert-report
All alerts, severity first then newest first (own stable merge sort).

### GET /analytics/devices/{device_id}/smoothed-temperature?window=5
```json
[{"timestamp": "2026-10-03T10:00:00", "temperature": 35.5, "smoothed": 34.8}]
```
Errors: 404 unknown device.
