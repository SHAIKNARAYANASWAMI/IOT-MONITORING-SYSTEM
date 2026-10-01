import queue
import threading
from datetime import datetime

from pydantic import ValidationError

from backend.app.database.session import SessionLocal
from backend.app.logging_config import get_logger
from backend.app.repositories.device_repository import DeviceRepository
from backend.app.repositories.reading_repository import ReadingRepository
from backend.app.schemas.telemetry import TelemetryIn

logger = get_logger("services.ingestion")


class IngestionService:
    """Producer-consumer: MQTT callback calls submit(); a worker thread processes."""

    def __init__(self, max_queue_size: int = 1000):
        # Bounded queue: if the worker falls behind, we drop instead of eating all memory.
        self.queue: queue.Queue = queue.Queue(maxsize=max_queue_size)
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._worker, name="ingestion-worker", daemon=True)
        self.processed = 0
        self.rejected = 0
        self.dropped = 0

    def start(self) -> None:
        self._thread.start()
        logger.info("Ingestion worker started")

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=3)

    def submit(self, topic: str, payload: dict) -> bool:
        """Called from the MQTT thread. Must be fast and never block."""
        try:
            self.queue.put_nowait(payload)
            return True
        except queue.Full:
            self.dropped += 1
            logger.error("Queue full, dropping message from %s", payload.get("device_id"))
            return False

    def _worker(self) -> None:
        while not self._stop.is_set():
            try:
                payload = self.queue.get(timeout=0.5)
            except queue.Empty:
                continue
            try:
                self.process(payload)
            except Exception:
                logger.exception("Unexpected error while processing message")
            finally:
                self.queue.task_done()

    def process(self, payload: dict) -> bool:
        """Validate, then save. Returns True if stored."""
        try:
            data = TelemetryIn(**payload)
        except ValidationError as exc:
            self.rejected += 1
            logger.warning("Invalid data from %s: %s", payload.get("device_id"), exc.errors()[0]["msg"])
            return False

        now = datetime.utcnow()
        db = SessionLocal()
        try:
            devices = DeviceRepository(db)
            if devices.get_by_device_id(data.device_id) is None:
                devices.add(data.device_id, name=data.device_id)
                logger.info("Auto-registered new device %s", data.device_id)

            ReadingRepository(db).add(
                device_id=data.device_id,
                timestamp=data.timestamp or now,
                temperature=data.temperature,
                humidity=data.humidity,
                voltage=data.voltage,
                current=data.current,
                pressure=data.pressure,
                battery=data.battery,
            )
            devices.update_status(data.device_id, "ONLINE", last_seen=now)
            self.processed += 1
            return True
        finally:
            db.close()