import json
import secrets

import uvicorn
from aiogram import Bot, Dispatcher, types
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from logfmt_logger import getLogger

from cost_my_chemo_bot.bots.telegram.bot import close_bot, init_bot, make_bot
from cost_my_chemo_bot.bots.telegram.dispatcher import make_dispatcher
from cost_my_chemo_bot.bots.telegram.storage import make_storage
from cost_my_chemo_bot.config import SETTINGS, WEBHOOK_SETTINGS
from cost_my_chemo_bot.db import DB

logger = getLogger(__name__)
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
    bot = Bot.get_current()
    dp = Dispatcher.get_current()
    await init_bot(bot, dp)


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
    bot = Bot.get_current()
    dp = Dispatcher.get_current()
    await close_bot(bot=bot, dp=dp)


if __name__ == "__main__":
    bot = make_bot()
    storage = make_storage()
    dp = make_dispatcher(bot, storage=storage)
    Bot.set_current(dp.bot)
    Dispatcher.set_current(dp)
    uvicorn.run(
        app,
        host=WEBHOOK_SETTINGS.WEBAPP_HOST,
        port=WEBHOOK_SETTINGS.WEBAPP_PORT,
    )
