import json
import time

import paho.mqtt.client as mqtt

from backend.app.config import get_settings
from backend.app.logging_config import get_logger, setup_logging

logger = get_logger("mqtt.subscriber")


class MqttSubscriber:
    """Connects to the broker, subscribes to telemetry, and hands each message to a callback."""

    def __init__(self, on_message_callback=None):
        self.settings = get_settings()
        self.on_message_callback = on_message_callback
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="iot-backend")
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        # Automatic reconnection with backoff if the broker goes down.
        self.client.reconnect_delay_set(min_delay=1, max_delay=30)

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            logger.info("Connected to MQTT broker, subscribing to %s", self.settings.mqtt_topic)
            # Subscribing inside on_connect means we re-subscribe after every reconnect.
            client.subscribe(self.settings.mqtt_topic, qos=1)
        else:
            logger.error("MQTT connection failed: %s", reason_code)

    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        logger.warning("Disconnected from MQTT broker (%s)", reason_code)

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            logger.error("Invalid JSON on topic %s: %s", msg.topic, exc)
            return
        logger.info("Received on %s: %s", msg.topic, payload)
        if self.on_message_callback:
            self.on_message_callback(msg.topic, payload)

    def start(self) -> None:
        self.client.connect(self.settings.mqtt_host, self.settings.mqtt_port, keepalive=30)
        self.client.loop_start()  # background thread

    def stop(self) -> None:
        self.client.loop_stop()
        self.client.disconnect()


if __name__ == "__main__":
    from backend.app.services.ingestion_service import IngestionService
    from backend.app.services.offline_detector import OfflineDetector

    setup_logging()
    ingestion = IngestionService()
    ingestion.start()
    detector = OfflineDetector()
    detector.start()
    subscriber = MqttSubscriber(on_message_callback=ingestion.submit)
    subscriber.start()
    logger.info("Subscriber + ingestion running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        subscriber.stop()
        detector.stop()
        ingestion.stop()
        logger.info("Stopped. processed=%s rejected=%s dropped=%s", ingestion.processed, ingestion.rejected, ingestion.dropped)