import enum
import logging

from pydantic import BaseSettings, Field, FilePath, HttpUrl


class BotMode(enum.Enum):
    POLLING = "polling"
    WEBHOOK = "webhook"


class Settings(BaseSettings):
    SERVICE_ACCOUNT_KEY: FilePath = Field("cost-my-chemo-bot-1319d9c83553.json")
    SPREADSHEET_URL: HttpUrl = "https://docs.google.com/spreadsheets/d/1xbSfnEiH3uUaqVwlFITPZNUgAk9vI0BOrQ-AnkYWhQ8/edit"
    WORKSHEET_ID: int = 1707048628
    TELEGRAM_BOT_TOKEN: str
    LOG_LEVEL: int = Field(logging.INFO)
    BOT_MODE: BotMode = BotMode.POLLING

    class Config:
        env_file = ".env"


class WebhookSettings(BaseSettings):
    # webhook settings
    WEBHOOK_HOST: str = "http://0.0.0.0:8080"
    WEBHOOK_PATH: str = "/api"

    # webserver settings
    WEBAPP_HOST: str = "0.0.0.0"  # or ip
    WEBAPP_PORT: int = 8080

    @property
    def webhook_url(self) -> str:
        return f"{self.WEBHOOK_HOST}{self.WEBHOOK_PATH}"

    class Config:
        env_file = ".env"


SETTINGS = Settings()
WEBHOOK_SETTINGS = None
if SETTINGS.BOT_MODE is BotMode.WEBHOOK:
    WEBHOOK_SETTINGS = WebhookSettings()
    print(WEBHOOK_SETTINGS.webhook_url)
