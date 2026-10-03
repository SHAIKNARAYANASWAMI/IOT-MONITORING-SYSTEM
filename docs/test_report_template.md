# Test Report

| Field | Value |
|---|---|
| Project | IoT Device Monitoring and Alert System |
| Date | |
| Tester | |
| Commit (git log --oneline -1) | |
| Python version | |
| OS | Windows |

## How to run
```
python -m pytest -v
cd cpp_device
g++ -std=c++17 -Wall -Wextra -o test_sensor.exe test_sensor.cpp sensor.cpp
.\test_sensor.exe
```

## Summary (fill in from real output)
| Suite | Tests run | Passed | Failed |
|---|---|---|---|
| Unit (rules, validation, DSA) | | | |
| Integration (services, API) | | | |
| C++ (assert tests) | | | |
| **Total** | | | |

## Manual tests
| ID | Scenario | Steps | Expected | Actual | Pass/Fail |
|---|---|---|---|---|---|
| M1 | Live data on dashboard | Start broker, API, subscriber, simulator; open `/` | Cards and table update every 3 s | | |
| M2 | Alert creation | Run simulator with `--fault-chance 0.5` | Alerts appear in table | | |
| M3 | Offline detection | Stop simulator, wait 40 s | Devices turn OFFLINE, alert raised | | |
| M4 | Offline recovery | Start simulator again | DEVICE_OFFLINE auto-resolves | | |
| M5 | Acknowledge | Click Acknowledge, log in | Status becomes ACKNOWLEDGED | | |
| M6 | Broker restart | Stop and start Mosquitto | Subscriber reconnects | | |

## Defects found
| ID | Description | Severity | Status |
|---|---|---|---|
| | | | |

## Notes
Only record results you actually observed.
