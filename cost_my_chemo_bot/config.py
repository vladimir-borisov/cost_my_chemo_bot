import enum
import logging

from pydantic import BaseSettings, Field, FilePath, HttpUrl, SecretStr


class BotMode(enum.Enum):
    POLLING = "polling"
    WEBHOOK = "webhook"


class StorageType(str, enum.Enum):
    JSON = "json"
    GCLOUD = "gcloud"


class Settings(BaseSettings):
    ONCO_MEDCONSULT_API_URL: HttpUrl = "http://onco.medconsult.ru/onco/hs/MobHTTP/api"
    ONCO_MEDCONSULT_API_LOGIN: str
    ONCO_MEDCONSULT_API_PASSWORD: SecretStr

    BITRIX_URL: HttpUrl = (
        "https://headache-hemonc.bitrix24.ru/rest/25/ztkgcrsxyths0h0u/crm.lead.add.json"
    )

    TELEGRAM_BOT_TOKEN: str
    LOG_LEVEL: int = Field(logging.INFO)
    BOT_MODE: BotMode = BotMode.POLLING
    SET_COMMANDS: bool = False

    STORAGE_TYPE: StorageType = StorageType.JSON

    class Config:
        env_file = ".env"


class WebhookSettings(BaseSettings):
    # webhook settings
    SET_WEBHOOK: bool = True
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


class JSONStorageSettings(BaseSettings):
    STATE_STORAGE_PATH: FilePath = "state.json"

    class Config:
        env_file = ".env"


SETTINGS = Settings()
WEBHOOK_SETTINGS = None
if SETTINGS.BOT_MODE is BotMode.WEBHOOK:
    WEBHOOK_SETTINGS = WebhookSettings()
if SETTINGS.STORAGE_TYPE is StorageType.JSON:
    JSON_STORAGE_SETTINGS = JSONStorageSettings()
