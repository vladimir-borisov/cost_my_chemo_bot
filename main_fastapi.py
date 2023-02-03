import json
import secrets

import uvicorn
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.files import JSONStorage
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from aiogram.dispatcher.filters import Command, Text
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from logfmt_logger import getLogger

from cost_my_chemo_bot.bots.telegram import filters
from cost_my_chemo_bot.bots.telegram.handlers import (
    back_handler,
    cancel_handler,
    init_handlers,
    process_category,
    process_category_invalid,
    process_height,
    process_height_invalid,
    process_nosology,
    process_nosology_invalid,
    process_weight,
    process_weight_invalid,
)
from cost_my_chemo_bot.bots.telegram.state import Form
from cost_my_chemo_bot.bots.telegram.storage import GcloudStorage
from cost_my_chemo_bot.config import (
    JSON_STORAGE_SETTINGS,
    SETTINGS,
    WEBHOOK_SETTINGS,
    StorageType,
)
from cost_my_chemo_bot.db import DB

logger = getLogger(__name__)


bot = Bot(token=SETTINGS.TELEGRAM_BOT_TOKEN)

match SETTINGS.STORAGE_TYPE:
    case StorageType.JSON:
        storage = JSONStorage(JSON_STORAGE_SETTINGS.STATE_STORAGE_PATH)
    case StorageType.GCLOUD:
        storage = GcloudStorage()
    case StorageType.REDIS:
        storage = RedisStorage2(
            host="redis-16916.c55.eu-central-1-1.ec2.cloud.redislabs.com",
            port=16916,
            db=0,
            username="cost_my_chemo_bot",
            password=SETTINGS.REDIS_PASSWORD,
        )
    case _:
        raise ValueError(f"Bullshit StorageType: {SETTINGS.STORAGE_TYPE}")

dp = Dispatcher(bot, storage=storage)
Bot.set_current(dp.bot)
Dispatcher.set_current(dp)


async def init_bot():
    getLogger("aiogram", level=SETTINGS.LOG_LEVEL)
    getLogger("uvicorn", level=SETTINGS.LOG_LEVEL)
    getLogger("asyncio", level=SETTINGS.LOG_LEVEL)

    if SETTINGS.SET_COMMANDS:
        await bot.set_my_commands(
            commands=[
                types.BotCommand(command="/start", description="Начать сначала"),
                types.BotCommand(command="/stop", description="Стоп"),
            ]
        )

    database = DB()
    Dispatcher.set_current(dp)
    Bot.set_current(bot)
    await database.load_db()
    if WEBHOOK_SETTINGS.SET_WEBHOOK:
        await bot.set_webhook(WEBHOOK_SETTINGS.webhook_url)

    init_handlers(dp)


app = FastAPI()
security = HTTPBasic()


async def check_creds(credentials: HTTPBasicCredentials = Depends(security)):
    current_username_bytes = credentials.username.encode("utf8")
    correct_username_bytes = SETTINGS.ONCO_MEDCONSULT_API_LOGIN.encode("utf8")
    is_correct_username = secrets.compare_digest(
        current_username_bytes, correct_username_bytes
    )
    current_password_bytes = credentials.password.encode("utf8")
    correct_password_bytes = (
        SETTINGS.ONCO_MEDCONSULT_API_PASSWORD.get_secret_value().encode("utf8")
    )
    is_correct_password = secrets.compare_digest(
        current_password_bytes, correct_password_bytes
    )
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@app.on_event("startup")
async def on_startup():
    await init_bot()


@app.post(WEBHOOK_SETTINGS.WEBHOOK_PATH)
async def bot_webhook(update: dict):
    telegram_update = types.Update(**update)
    Dispatcher.set_current(dp)
    Bot.set_current(bot)
    results = await dp.process_update(telegram_update)
    results = [json.loads(r.get_web_response().body) for r in results]
    logger.info(f"results={results}")
    if not results:
        result = {}
    else:
        result = results[0]
    return result


@app.get("/db/courses/")
async def get_db_courses(credentials: HTTPBasicCredentials = Depends(check_creds)):
    return DB().courses


@app.get("/db/nosologies/")
async def get_db_nosologies(credentials: HTTPBasicCredentials = Depends(check_creds)):
    return DB().courses


@app.get("/db/categories/")
async def get_db_categories(credentials: HTTPBasicCredentials = Depends(check_creds)):
    return DB().categories


@app.post("/db/reload/")
async def reload_db(credentials: HTTPBasicCredentials = Depends(check_creds)):
    await DB().reload_db()
    return {"ok": True}


@app.on_event("shutdown")
async def on_shutdown():
    Dispatcher.set_current(dp)
    Bot.set_current(bot)
    await dp.storage.close()
    await dp.storage.wait_closed()
    await DB.close()
    session = await dp.bot.get_session()
    await session.close()


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=WEBHOOK_SETTINGS.WEBAPP_HOST,
        port=WEBHOOK_SETTINGS.WEBAPP_PORT,
    )
