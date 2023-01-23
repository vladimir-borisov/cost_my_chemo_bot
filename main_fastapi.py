import json

import uvicorn
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.filters import Command, Text
from cache import AsyncLRU
from fastapi import FastAPI
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
from cost_my_chemo_bot.config import SETTINGS, WEBHOOK_SETTINGS
from cost_my_chemo_bot.db import DB

logger = getLogger(__name__)


async def register_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(
        cancel_handler, Text(equals=["stop"], ignore_case=True), state="*"
    )
    dp.register_message_handler(cancel_handler, Command(commands=["stop"]), state="*")

    dp.register_callback_query_handler(back_handler, filters.back_valid, state="*")
    dp.register_message_handler(back_handler, filters.back_valid, state="*")

    dp.register_callback_query_handler(
        process_category, filters.category_valid, state=Form.category
    )

    dp.register_callback_query_handler(
        process_category_invalid, filters.category_invalid, state=Form.category
    )

    dp.register_message_handler(process_height, filters.height_valid, state=Form.height)

    dp.register_message_handler(
        process_height_invalid, filters.height_invalid, state=Form.height
    )

    dp.register_callback_query_handler(
        process_nosology, filters.nosology_valid, state=Form.nosology
    )

    dp.register_callback_query_handler(
        process_nosology_invalid, filters.nosology_invalid, state=Form.nosology
    )

    dp.register_message_handler(process_weight, filters.weight_valid, state=Form.weight)

    dp.register_message_handler(
        process_weight_invalid, filters.weight_invalid, state=Form.weight
    )

    init_handlers(dp)


@AsyncLRU(maxsize=1)
async def init_bot() -> Dispatcher:
    getLogger("aiogram", level=SETTINGS.LOG_LEVEL)
    getLogger("uvicorn", level=SETTINGS.LOG_LEVEL)
    getLogger("asyncio", level=SETTINGS.LOG_LEVEL)

    database = DB()
    await database.load_db()
    bot = Bot(token=SETTINGS.TELEGRAM_BOT_TOKEN)
    if WEBHOOK_SETTINGS.SET_WEBHOOK:
        await bot.set_webhook(WEBHOOK_SETTINGS.webhook_url)
    storage = GcloudStorage()
    dp = Dispatcher(bot, storage=storage)
    Bot.set_current(dp.bot)
    Dispatcher.set_current(dp)

    await register_handlers(dp)
    return dp


app = FastAPI()


@app.on_event("startup")
async def on_startup():
    _ = await init_bot()


@app.post(WEBHOOK_SETTINGS.WEBHOOK_PATH)
async def bot_webhook(update: dict):
    telegram_update = types.Update(**update)
    dp = await init_bot()
    results = await dp.process_update(telegram_update)
    results = [json.loads(r.get_web_response().body) for r in results]
    logger.info(f"results={results}")
    if not results:
        result = {}
    else:
        result = results[0]
    return result


@app.get("/db/courses/")
async def get_db_courses():
    return DB().courses


@app.get("/db/nosologies/")
async def get_db_nosologies():
    return DB().courses


@app.get("/db/categories/")
async def get_db_categories():
    return DB().categories


@app.post("/db/reload/")
async def reload_db():
    await DB().reload_db()
    return {"ok": True}


@app.on_event("shutdown")
async def on_shutdown():
    dp = await init_bot()
    await dp.storage.close()
    await DB.close()
    session = await dp.bot.get_session()
    await session.close()


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=WEBHOOK_SETTINGS.WEBAPP_HOST,
        port=WEBHOOK_SETTINGS.WEBAPP_PORT,
    )
