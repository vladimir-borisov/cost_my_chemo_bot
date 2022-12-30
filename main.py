import asyncio
import json
import logging

import functions_framework
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.filters import Command, CommandStart, Text
from flask import Request

from cost_my_chemo_bot.bots.telegram import filters
from cost_my_chemo_bot.bots.telegram.handlers import (
    back_handler,
    cancel_handler,
    process_category,
    process_category_invalid,
    process_course,
    process_course_invalid,
    process_height,
    process_height_invalid,
    process_lead,
    process_nosology,
    process_nosology_invalid,
    process_weight,
    process_weight_invalid,
    welcome_handler,
)
from cost_my_chemo_bot.bots.telegram.state import Form
from cost_my_chemo_bot.bots.telegram.storage import GcloudStorage
from cost_my_chemo_bot.config import SETTINGS
from cost_my_chemo_bot.db import DB


async def register_handlers(dp: Dispatcher):
    dp.register_message_handler(
        welcome_handler,
        CommandStart(),
        filters.welcome_message,
        filters.welcome_message_text,
        state="*",
    )
    dp.register_callback_query_handler(
        welcome_handler, filters.welcome_callback, state="*"
    )

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

    dp.register_callback_query_handler(
        process_course, filters.course_valid, state=Form.course
    )

    dp.register_callback_query_handler(
        process_course_invalid, filters.course_invalid, state=Form.course
    )

    dp.register_message_handler(process_height, filters.height_valid, state=Form.height)

    dp.register_message_handler(
        process_height_invalid, filters.height_invalid, state=Form.height
    )

    dp.register_message_handler(
        process_lead, state=Form.lead, content_types=types.ContentType.CONTACT
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


async def process_event(event) -> dict:
    """
    Converting an AWS Lambda event to an update and handling that
    update.
    """

    logging.debug("Update: " + str(event))

    bot = Bot(token=SETTINGS.TELEGRAM_BOT_TOKEN)
    storage = GcloudStorage()
    # storage = FirestoreStorage()
    dp = Dispatcher(bot, storage=storage)
    Bot.set_current(dp.bot)
    Dispatcher.set_current(dp)
    await register_handlers(dp)
    Bot.set_current(dp.bot)
    database = DB()
    await database.load_db()
    update = types.Update.to_object(event)
    print(f"new_update={update}")
    results = await dp.process_update(update)
    results = [json.loads(r.get_web_response().body) for r in results]
    print(f"results={results}")
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
