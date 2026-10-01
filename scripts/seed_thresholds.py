from backend.app.database.session import SessionLocal
from backend.app.repositories.threshold_repository import ThresholdRepository

# metric: (min, max, severity)
DEFAULTS = {
    "temperature": (5, 50, "CRITICAL"),
    "voltage": (200, 250, "CRITICAL"),
    "current": (None, 10, "WARNING"),
    "battery": (20, None, "WARNING"),
    "humidity": (10, 90, "INFO"),
    "pressure": (95, 105, "INFO"),
}


def seed() -> None:
    db = SessionLocal()
    try:
        repo = ThresholdRepository(db)
        for metric, (low, high, severity) in DEFAULTS.items():
            repo.upsert(metric, min_value=low, max_value=high, severity=severity)
        print("Default thresholds:")
        for t in repo.list_all():
            print(f" - {t.metric}: min={t.min_value} max={t.max_value} severity={t.severity}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()