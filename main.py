import asyncio
import json

import functions_framework
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.filters import Command, Text
from flask import Request
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
from cost_my_chemo_bot.config import SETTINGS
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


async def init_bot() -> Dispatcher:
    getLogger("aiogram", level=SETTINGS.LOG_LEVEL)

    database = DB()
    await database.load_db()
    bot = Bot(token=SETTINGS.TELEGRAM_BOT_TOKEN)
    storage = GcloudStorage()
    dp = Dispatcher(bot, storage=storage)
    Bot.set_current(dp.bot)
    Dispatcher.set_current(dp)

    await register_handlers(dp)
    return dp


async def process_event(event) -> dict:
    """
    Converting an AWS Lambda event to an update and handling that
    update.
    """

    logger.info("Update: " + str(event))

    dp = await init_bot()

    update = types.Update.to_object(event)
    logger.info(f"new_update={update}")
    results = await dp.process_update(update)
    results = [json.loads(r.get_web_response().body) for r in results]
    logger.info(f"results={results}")
    if not results:
        result = {}
    else:
        result = results[0]
    await dp.storage.close()
    await dp.storage.wait_closed()
    return result


@functions_framework.http
def process_webhook(request: Request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
    """
    request_json = request.get_json(silent=True)
    if request_json is None:
        request_json = {}

    return asyncio.new_event_loop().run_until_complete(
        process_event(event=request_json)
    )
