from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "sqlite+pysqlite:///./cabinet.db"
    jwt_secret: str = "change-me-in-production-demo-only"
    jwt_ttl_minutes: int = 720
    pipeline_step_delay_sec: float = 1.2
    cors_origins: str = "http://localhost:8080,http://localhost:5173"
    seed_on_start: bool = True
    ml_service_url: str = "http://ml-service:8100"
    ml_request_timeout: float = 2.0
    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]
settings = Settings()