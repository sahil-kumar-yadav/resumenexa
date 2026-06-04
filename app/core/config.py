from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    log_level: str = "INFO"

    upload_dir: str = "./uploads"
    max_upload_mb: int = 20

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:latest"

    @property
    def max_upload_bytes(self) -> int:
        return int(self.max_upload_mb) * 1024 * 1024


settings = Settings()

