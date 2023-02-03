import asyncio
import json

import functions_framework
from aiogram import Bot, Dispatcher, types
from flask import Request
from logfmt_logger import getLogger

from cost_my_chemo_bot.bots.telegram.handlers import init_handlers
from cost_my_chemo_bot.bots.telegram.storage import GcloudStorage
from cost_my_chemo_bot.config import SETTINGS
from cost_my_chemo_bot.db import DB

logger = getLogger(__name__)


async def init_bot() -> Dispatcher:
    getLogger("aiogram", level=SETTINGS.LOG_LEVEL)

    database = DB()
    await database.load_db()
    bot = Bot(token=SETTINGS.TELEGRAM_BOT_TOKEN)
    storage = GcloudStorage()
    dp = Dispatcher(bot, storage=storage)
    Bot.set_current(dp.bot)
    Dispatcher.set_current(dp)

    init_handlers(dp)
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
    session = await dp.bot.get_session()
    await session.close()
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
