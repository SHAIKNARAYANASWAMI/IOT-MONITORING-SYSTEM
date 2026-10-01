import argparse
import json
import time

from device_simulator.device import SimulatedDevice


def build_devices(count: int, fault_chance: float) -> list[SimulatedDevice]:
    return [SimulatedDevice(f"DEVICE-{i:03d}", fault_chance) for i in range(1, count + 1)]


def run(count: int, interval: float, fault_chance: float, cycles: int | None) -> None:
    devices = build_devices(count, fault_chance)
    print(f"Simulating {count} device(s), interval={interval}s. Press Ctrl+C to stop.")

    cycle = 0
    try:
        while cycles is None or cycle < cycles:
            for device in devices:
                reading = device.generate_reading()
                if reading is None:
                    print(f"{device.device_id}: OFFLINE (no data sent)")
                else:
                    print(json.dumps(reading))
            cycle += 1
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nSimulator stopped.")


def main() -> None:
    parser = argparse.ArgumentParser(description="IoT device simulator")
    parser.add_argument("--devices", type=int, default=5, help="number of devices")
    parser.add_argument("--interval", type=float, default=2.0, help="seconds between readings")
    parser.add_argument("--fault-chance", type=float, default=0.1, help="fault probability 0 to 1")
    parser.add_argument("--cycles", type=int, default=None, help="stop after N cycles")
    args = parser.parse_args()
    run(args.devices, args.interval, args.fault_chance, args.cycles)


if __name__ == "__main__":
    main()