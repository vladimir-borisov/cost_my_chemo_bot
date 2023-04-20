import enum
import logging

from pydantic import BaseSettings, Field, FilePath, HttpUrl, SecretStr


class BotMode(enum.Enum):
    POLLING = "polling"
    WEBHOOK = "webhook"


class StorageType(str, enum.Enum):
    JSON = "json"
    GCLOUD = "gcloud"
    REDIS = "redis"


class Settings(BaseSettings):
    ONCO_MEDCONSULT_API_URL: HttpUrl = "http://onco.medconsult.ru/onco/hs/MobHTTP/api"
    ONCO_MEDCONSULT_API_LOGIN: str
    ONCO_MEDCONSULT_API_PASSWORD: SecretStr

    BITRIX_URL: HttpUrl = "https://headache-hemonc.bitrix24.ru/rest/25"
    BITRIX_TOKEN: SecretStr

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
    HOST: str = "0.0.0.0"  # or ip
    PORT: int = 8080
    RELOAD: bool = False

    @property
    def webhook_url(self) -> str:
        return f"{self.WEBHOOK_HOST}{self.WEBHOOK_PATH}"

    class Config:
        env_file = ".env"


class JSONStorageSettings(BaseSettings):
    STATE_STORAGE_PATH: FilePath = "storage.json"

    class Config:
        env_file = ".env"


class RedisSettings(BaseSettings):
    REDIS_HOST: str = "redis-16916.c55.eu-central-1-1.ec2.cloud.redislabs.com"
    REDIS_PORT: int = 16916
    REDIS_DB: int = 0
    REDIS_USERNAME: str = "cost_my_chemo_bot"
    REDIS_PASSWORD: str = ""
    STATE_TTL: int | None = 60 * 60 * 24 * 1  # 1 day.
    DATA_TTL: int | None = 60 * 60 * 24 * 1  # 1 day.
    BUCKET_TTL: int | None = 60 * 60 * 24 * 1  # 1 day.

    class Config:
        env_file = ".env"


class ActionLoggerSettings(BaseSettings):

    ACTION_LOGGER_BASE_URL: str = "https://logsene-receiver.eu.sematext.com"
    ACTION_LOGGER_TOKEN: str = ""
    ACTION_LOGGER_NAME: str = "CHEMO_BOT"  # by this name we can determine where log came from

    @property
    def get_api_url(self) -> str:
        """ Get correct url for api call"""
        return f"{self.ACTION_LOGGER_BASE_URL}/{self.ACTION_LOGGER_TOKEN}/{self.ACTION_LOGGER_NAME}"

    class Config:
        env_file = ".env"


SETTINGS = Settings()
WEBHOOK_SETTINGS = None
if SETTINGS.BOT_MODE is BotMode.WEBHOOK:
    WEBHOOK_SETTINGS = WebhookSettings()

JSON_STORAGE_SETTINGS = None
if SETTINGS.STORAGE_TYPE is StorageType.JSON:
    JSON_STORAGE_SETTINGS = JSONStorageSettings()

REDIS_SETTINGS = None
if SETTINGS.STORAGE_TYPE is StorageType.REDIS:
    REDIS_SETTINGS = RedisSettings()

ACTION_LOGGER_SETTINGS = ActionLoggerSettings()