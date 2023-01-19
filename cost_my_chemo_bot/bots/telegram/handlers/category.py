from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.webhook import SendMessage
from logfmt_logger import getLogger

from cost_my_chemo_bot.bots.telegram import dispatcher, filters, messages
from cost_my_chemo_bot.bots.telegram.keyboard import get_keyboard_markup
from cost_my_chemo_bot.bots.telegram.send import send_message
from cost_my_chemo_bot.bots.telegram.state import Form
from cost_my_chemo_bot.db import DB

logger = getLogger(__name__)
database = DB()


@dispatcher.dp.callback_query_handler(filters.category_valid, state=Form.category)
async def process_category(
    callback: types.CallbackQuery, state: FSMContext
) -> types.Message | SendMessage:
    message = callback.message
    await state.update_data(category_id=callback.data)
    await state.set_state(Form.nosology)
    return await dispatcher.send_nosology_message(message=message, state=state)


@dispatcher.dp.callback_query_handler(filters.category_invalid, state=Form.category)
async def process_category_invalid(
    callback: types.CallbackQuery,
) -> types.Message | SendMessage:
    return await send_message(
        dispatcher.bot,
        chat_id=callback.message.chat.id,
        text=messages.CATEGORY_WRONG,
        reply_markup=get_keyboard_markup(buttons=sorted(database.categories)),
    )
