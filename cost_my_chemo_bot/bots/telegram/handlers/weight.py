import logging

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.webhook import SendMessage

from cost_my_chemo_bot.bots.telegram import dispatcher, filters, messages
from cost_my_chemo_bot.bots.telegram.keyboard import get_keyboard_markup
from cost_my_chemo_bot.bots.telegram.send import send_message
from cost_my_chemo_bot.bots.telegram.state import Form

logger = logging.getLogger(__name__)


@dispatcher.dp.message_handler(filters.weight_valid, state=Form.weight)
async def process_weight(
    message: types.Message, state: FSMContext
) -> types.Message | SendMessage:
    await state.update_data(weight=int(message.text))
    await state.set_state(Form.category)
    return await dispatcher.send_category_message(message=message)


@dispatcher.dp.message_handler(filters.weight_invalid, state=Form.weight)
async def process_weight_invalid(message: types.Message):
    return await send_message(
        dispatcher.bot,
        chat_id=message.chat.id,
        text=messages.WEIGHT_WRONG,
        reply_markup=get_keyboard_markup(),
    )
