from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="HCDMAP_", extra="ignore")

    db_url: str = "mysql+pymysql://hcdmap:hcdmap@localhost:3306/hcdmap"
    store_id: str = "store-001"
    mqtt_host: str = "localhost"
    mqtt_port: int = 1883
    service_token: str = "dev-service-token"
    jwt_secret: str = "dev-jwt-secret-change-me"
    floorplan_dir: str = "data/floorplans"
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
