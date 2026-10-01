from sqlalchemy.orm import Session

from backend.app.logging_config import get_logger
from backend.app.repositories.alert_repository import AlertRepository
from backend.app.repositories.threshold_repository import ThresholdRepository
from backend.app.rules.rules import ALL_RULES

logger = get_logger("services.alert")


class AlertService:
    """Runs every rule on a reading, creates alerts, avoids duplicates, auto-resolves."""

    def __init__(self, db: Session):
        self.alerts = AlertRepository(db)
        self.thresholds = ThresholdRepository(db)

    def check_reading(self, device_id: str, values: dict) -> list:
        """values example: {'temperature': 62.0, 'battery': 7, ...}. Returns newly created alerts."""
        created = []

        # Device is sending data, so any DEVICE_OFFLINE alert is no longer true.
        offline = self.alerts.find_active(device_id, "DEVICE_OFFLINE")
        if offline is not None:
            self.alerts.resolve(offline.id)
            logger.info("Alert DEVICE_OFFLINE on %s auto-resolved (data received)", device_id)

        for rule in ALL_RULES:
            threshold = self.thresholds.get_effective(rule.metric, device_id)
            if threshold is None:
                continue

            candidate = rule.evaluate(
                values.get(rule.metric),
                threshold.min_value,
                threshold.max_value,
                threshold.severity,
            )

            if candidate is not None:
                # Only create if no active alert of this type already exists.
                if self.alerts.find_active(device_id, candidate.alert_type) is None:
                    alert = self.alerts.add(
                        device_id,
                        candidate.alert_type,
                        candidate.severity,
                        candidate.actual_value,
                        candidate.threshold_value,
                    )
                    created.append(alert)
                    logger.warning(
                        "ALERT %s on %s: value=%s limit=%s (%s)",
                        candidate.alert_type, device_id,
                        candidate.actual_value, candidate.threshold_value, candidate.severity,
                    )
            elif values.get(rule.metric) is not None:
                # Metric is back to normal: resolve any active alert for this metric.
                for alert_type in (rule.high_alert, rule.low_alert):
                    if not alert_type:
                        continue
                    active = self.alerts.find_active(device_id, alert_type)
                    if active is not None:
                        self.alerts.resolve(active.id)
                        logger.info("Alert %s on %s auto-resolved", alert_type, device_id)
        return created