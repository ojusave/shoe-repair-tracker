from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "sqlite:///./local.db"
    TWILIO_ACCOUNT_SID: str | None = None
    TWILIO_AUTH_TOKEN: str | None = None
    TWILIO_FROM_NUMBER: str | None = None
    STORE_NAME: str = "the shop"
    REMINDER_AFTER_DAYS: int = 3
    REMINDER_INTERVAL_DAYS: int = 3


settings = Settings()
