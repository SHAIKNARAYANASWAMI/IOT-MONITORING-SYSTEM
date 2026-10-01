import argparse
import json
import time

import paho.mqtt.client as mqtt

from device_simulator.device import SimulatedDevice


def build_devices(count: int, fault_chance: float) -> list[SimulatedDevice]:
    return [SimulatedDevice(f"DEVICE-{i:03d}", fault_chance) for i in range(1, count + 1)]


def make_client(host: str, port: int) -> mqtt.Client:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="iot-simulator")

    def on_connect(client, userdata, flags, reason_code, properties):
        print(f"Connected to broker {host}:{port} (code: {reason_code})")

    def on_disconnect(client, userdata, flags, reason_code, properties):
        print(f"Disconnected from broker (code: {reason_code}). Will auto-reconnect.")

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    # If the broker goes down, paho retries automatically with this backoff.
    client.reconnect_delay_set(min_delay=1, max_delay=30)
    client.connect(host, port, keepalive=30)
    client.loop_start()  # network loop runs in a background thread
    return client


def run(count: int, interval: float, fault_chance: float, cycles: int | None, host: str, port: int) -> None:
    devices = build_devices(count, fault_chance)
    client = make_client(host, port)
    print(f"Simulating {count} device(s), interval={interval}s. Press Ctrl+C to stop.")

    cycle = 0
    try:
        while cycles is None or cycle < cycles:
            for device in devices:
                reading = device.generate_reading()
                if reading is None:
                    print(f"{device.device_id}: OFFLINE (no data sent)")
                    continue
                topic = f"iot/devices/{device.device_id}/telemetry"
                client.publish(topic, json.dumps(reading), qos=1)
                print(f"Published to {topic}: temp={reading['temperature']} battery={reading['battery']}")
            cycle += 1
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nSimulator stopped.")
    finally:
        client.loop_stop()
        client.disconnect()


def main() -> None:
    parser = argparse.ArgumentParser(description="IoT device simulator (MQTT publisher)")
    parser.add_argument("--devices", type=int, default=5, help="number of devices")
    parser.add_argument("--interval", type=float, default=2.0, help="seconds between readings")
    parser.add_argument("--fault-chance", type=float, default=0.1, help="fault probability 0 to 1")
    parser.add_argument("--cycles", type=int, default=None, help="stop after N cycles")
    parser.add_argument("--host", default="localhost", help="MQTT broker host")
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port")
    args = parser.parse_args()
    run(args.devices, args.interval, args.fault_chance, args.cycles, args.host, args.port)


if __name__ == "__main__":
    main()