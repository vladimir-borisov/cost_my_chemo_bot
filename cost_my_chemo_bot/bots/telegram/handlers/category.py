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


@dispatcher.dp.callback_query_handler(
    lambda callback: callback.data in database.categories, state=Form.category
)
async def process_category(
    callback: types.CallbackQuery, state: FSMContext
) -> types.Message | SendMessage:
    message = callback.message
    await state.update_data(category=callback.data)
    await state.set_state(Form.subcategory)
    return await dispatcher.send_subcategory_message(message=message, state=state)


@dispatcher.dp.message_handler(
    filters.category_invalid,
    state=Form.category,
)
async def process_category_invalid(
    message: types.Message,
) -> types.Message | SendMessage:
    return await send_message(
        dispatcher.bot,
        chat_id=message.chat.id,
        text=messages.CATEGORY_WRONG,
        reply_markup=get_keyboard_markup(buttons=sorted(database.categories)),
    )
