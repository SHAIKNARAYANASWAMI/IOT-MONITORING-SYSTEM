# Demo Script (about 5 minutes)

## Before the interview (10 minutes earlier)
1. If port 1883 is busy, stop the Windows service from an admin PowerShell: `net stop mosquitto`.
2. Open 4 terminals, each in the project folder, venv active in the Python ones:
   - T1 Broker: `& "C:\Program Files\mosquitto\mosquitto.exe" -c mosquitto.conf -v`
   - T2 API: `python -m uvicorn backend.app.main:app --reload`
   - T3 Subscriber: `python -m backend.app.mqtt.subscriber`
   - T4 Simulator (start later, during the demo)
3. Open `http://127.0.0.1:8000/` and `http://127.0.0.1:8000/docs` in two tabs.
4. Run `python -m pytest -v` once so you know it passes.
5. Keep VS Code open on `rule engine`, `ingestion_service.py`, `ring_buffer.py`.

## Minute 0-1: the idea
"This monitors many IoT devices in real time. Devices publish readings over MQTT, the backend validates and stores them, a rule engine raises alerts, and the dashboard shows live status. Devices are simulated, not real hardware."
Show the architecture diagram in README.md.

## Minute 1-2: live data
- Start the simulator in T4:
  `python -m device_simulator.simulator --devices 5 --interval 2 --fault-chance 0.15`
- Point at the dashboard: cards, device table updating every 3 seconds.
- Click a device row: charts change.
- Say: "The simulator publishes to `iot/devices/{id}/telemetry`. The broker routes it to my subscriber."

## Minute 2-3: alerts
- Point at the alerts table (low battery, high current, and so on).
- Click Acknowledge, log in as admin, show status change.
- Say: "One active alert per device and type, so no alert storms. When the value returns to normal it auto-resolves."

## Minute 3-4: offline detection
- Stop the simulator (Ctrl+C). Wait about 40 seconds.
- Devices turn OFFLINE (grey) with a DEVICE_OFFLINE alert. Restart the simulator and show it resolve.
- Say: "A background thread scans last_seen every 5 seconds against a 30 second timeout."

## Minute 4-5: code and quality
- Open `/docs`: show POST /telemetry with value 9999, get 422. Show an endpoint without a token, get 401.
- Open `ingestion_service.py`: explain the bounded queue and worker thread.
- Open `ring_buffer.py`: explain wrap-around, O(1) insert.
- Show the `pytest` result and mention the 12 C++ tests.
- Say: "The C++ module is a standalone PC program showing bit flags and fixed buffers. It is not firmware."

## If something fails live
- No data on dashboard: check T3 shows "Received", then the broker, then the simulator. Narrate it: this is the debugging method.
- Port 1883 busy: `net stop mosquitto` in admin PowerShell.
- Do not panic. Explaining how you debug is itself a good answer.

## Questions to expect after the demo
Why MQTT? Why a queue? How would you scale to 10,000 devices? What are the weak points? Practise these from INTERVIEW_PREPARATION.md.
