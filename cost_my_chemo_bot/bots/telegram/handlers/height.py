import logging

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.webhook import SendMessage

from cost_my_chemo_bot.bots.telegram import dispatcher, filters, messages
from cost_my_chemo_bot.bots.telegram.keyboard import get_keyboard_markup
from cost_my_chemo_bot.bots.telegram.send import send_message
from cost_my_chemo_bot.bots.telegram.state import Form
from cost_my_chemo_bot.db import DB

logger = logging.getLogger(__name__)
database = DB()


@dispatcher.dp.message_handler(filters.height_valid, state=Form.height)
async def process_height(
    message: types.Message, state: FSMContext
) -> types.Message | SendMessage:
    await state.update_data(height=int(message.text))
    await state.set_state(Form.weight)
    return await dispatcher.send_weight_message(message=message)


@dispatcher.dp.message_handler(filters.height_invalid, state=Form.height)
async def process_height_invalid(message: types.Message):
    return await send_message(
        dispatcher.bot,
        chat_id=message.chat.id,
        text=messages.HEIGHT_WRONG,
        reply_markup=get_keyboard_markup(),
    )
