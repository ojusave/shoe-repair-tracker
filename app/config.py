from pydantic import field_validator
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

    @field_validator(
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN",
        "TWILIO_FROM_NUMBER",
        mode="before",
    )
    @classmethod
    def empty_str_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("STORE_NAME", mode="before")
    @classmethod
    def default_store_name(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return "the shop"
        return value


settings = Settings()
