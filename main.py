import asyncio
import logging

import functions_framework
from aiogram import types
from flask import Request

from cost_my_chemo_bot.bots.telegram.main import dp
from cost_my_chemo_bot.db import DB


async def process_event(event):
    """
    Converting an AWS Lambda event to an update and handling that
    update.
    """

    logging.debug("Update: " + str(event))

    # Bot.set_current(dp.bot)
    database = DB()
    await database.load_db()
    update = types.Update.to_object(event)
    await dp.process_update(update)
    await dp.storage.close()
    await dp.storage.wait_closed()


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
    request_args = request.args

    asyncio.run(process_event(event=request_json))

    return "ok"
