from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "IoT Monitoring System"
    database_url: str = "sqlite:///./iot.db"

    mqtt_host: str = "localhost"
    mqtt_port: int = 1883
    mqtt_username: str = ""
    mqtt_password: str = ""
    mqtt_topic: str = "iot/devices/+/telemetry"

    offline_timeout_seconds: int = 30
    jwt_secret: str = "dev-secret-change-me"
    jwt_expire_minutes: int = 60
    log_level: str = "INFO"

    admin_username: str = "admin"
    admin_password: str = "admin123"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()