import random
from datetime import datetime, timezone


class SimulatedDevice:
    """One fake IoT device that produces sensor readings."""

    def __init__(self, device_id: str, fault_chance: float = 0.1):
        self.device_id = device_id
        self.fault_chance = fault_chance  # probability of a fault per reading
        self.battery = random.randint(60, 100)
        self.online = True

    def _normal_reading(self) -> dict:
        return {
            "temperature": round(random.uniform(25, 40), 1),
            "humidity": round(random.uniform(40, 70), 1),
            "voltage": round(random.uniform(225, 235), 1),
            "current": round(random.uniform(2, 6), 1),
            "pressure": round(random.uniform(100, 102), 1),
        }

    def _apply_fault(self, data: dict) -> dict:
        """Randomly break one value so the alert engine has something to detect."""
        fault = random.choice(["high_temp", "high_current", "bad_voltage", "low_battery"])
        if fault == "high_temp":
            data["temperature"] = round(random.uniform(55, 80), 1)
        elif fault == "high_current":
            data["current"] = round(random.uniform(12, 20), 1)
        elif fault == "bad_voltage":
            data["voltage"] = round(random.choice([random.uniform(150, 190), random.uniform(260, 290)]), 1)
        elif fault == "low_battery":
            self.battery = random.randint(5, 15)
        return data

    def go_offline(self) -> None:
        self.online = False

    def go_online(self) -> None:
        self.online = True

    def generate_reading(self) -> dict | None:
        """Returns a reading, or None if the device is offline (sends nothing)."""
        if not self.online:
            return None

        data = self._normal_reading()
        if random.random() < self.fault_chance:
            data = self._apply_fault(data)

        # Battery slowly drains
        self.battery = max(0, self.battery - random.choice([0, 0, 0, 1]))

        data.update(
            {
                "device_id": self.device_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "battery": self.battery,
                "status": "ONLINE",
            }
        )
        return data