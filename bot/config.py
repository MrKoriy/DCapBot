from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    bot_token: str
    database_url: str
    channel_id: int
    admin_ids: list[int]
    bot_username: str

    plan_1_name: str
    plan_1_price: int
    plan_1_days: int

    plan_3_name: str
    plan_3_price: int
    plan_3_days: int

    yookassa_shop_id: str
    yookassa_secret_key: str

    @property
    def plans(self) -> list[dict[str, str | int]]:
        return [
            {"name": self.plan_1_name, "price": self.plan_1_price, "days": self.plan_1_days},
            {"name": self.plan_3_name, "price": self.plan_3_price, "days": self.plan_3_days},
        ]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Lazily instantiate settings singleton. Use this instead of module-level access."""
    return Settings()
