from dataclasses import dataclass


@dataclass
class AlertCandidate:
    """What a rule returns when a condition is violated."""
    alert_type: str
    severity: str
    actual_value: float
    threshold_value: float


class Rule:
    """Base class. Each rule checks ONE metric against its min/max limits."""

    metric: str = ""
    high_alert: str = ""
    low_alert: str = ""

    def evaluate(self, value, min_value, max_value, severity):
        if value is None:
            return None
        if max_value is not None and self.high_alert and value > max_value:
            return AlertCandidate(self.high_alert, severity, value, max_value)
        if min_value is not None and self.low_alert and value < min_value:
            return AlertCandidate(self.low_alert, severity, value, min_value)
        return None


class TemperatureRule(Rule):
    metric = "temperature"
    high_alert = "HIGH_TEMPERATURE"
    low_alert = "LOW_TEMPERATURE"


class VoltageRule(Rule):
    metric = "voltage"
    high_alert = "HIGH_VOLTAGE"
    low_alert = "LOW_VOLTAGE"


class CurrentRule(Rule):
    metric = "current"
    high_alert = "HIGH_CURRENT"


class BatteryRule(Rule):
    metric = "battery"
    low_alert = "LOW_BATTERY"


class HumidityRule(Rule):
    metric = "humidity"
    high_alert = "HIGH_HUMIDITY"
    low_alert = "LOW_HUMIDITY"


class PressureRule(Rule):
    metric = "pressure"
    high_alert = "HIGH_PRESSURE"
    low_alert = "LOW_PRESSURE"


ALL_RULES = [
    TemperatureRule(),
    VoltageRule(),
    CurrentRule(),
    BatteryRule(),
    HumidityRule(),
    PressureRule(),
]