from backend.app.rules.rules import BatteryRule, CurrentRule, TemperatureRule


def test_high_temperature_creates_candidate():
    c = TemperatureRule().evaluate(62, 5, 50, "CRITICAL")
    assert c.alert_type == "HIGH_TEMPERATURE"
    assert c.actual_value == 62
    assert c.threshold_value == 50
    assert c.severity == "CRITICAL"


def test_low_temperature_creates_candidate():
    c = TemperatureRule().evaluate(2, 5, 50, "CRITICAL")
    assert c.alert_type == "LOW_TEMPERATURE"
    assert c.threshold_value == 5


def test_normal_temperature_returns_none():
    assert TemperatureRule().evaluate(30, 5, 50, "CRITICAL") is None


def test_missing_value_returns_none():
    assert TemperatureRule().evaluate(None, 5, 50, "CRITICAL") is None


def test_value_exactly_at_limit_is_not_an_alert():
    assert TemperatureRule().evaluate(50, 5, 50, "CRITICAL") is None


def test_low_battery():
    c = BatteryRule().evaluate(7, 20, None, "WARNING")
    assert c.alert_type == "LOW_BATTERY"


def test_current_only_has_high_limit():
    assert CurrentRule().evaluate(15, None, 10, "WARNING").alert_type == "HIGH_CURRENT"
    assert CurrentRule().evaluate(0, None, 10, "WARNING") is None