import logging

from aiogram import types
from aiogram.dispatcher import FSMContext

from cost_my_chemo_bot.bots.telegram import dispatcher, filters, messages
from cost_my_chemo_bot.bots.telegram.keyboard import get_keyboard_markup
from cost_my_chemo_bot.bots.telegram.send import send_message
from cost_my_chemo_bot.bots.telegram.state import Form, parse_state
from cost_my_chemo_bot.db import DB

logger = logging.getLogger(__name__)
database = DB()


@dispatcher.dp.callback_query_handler(filters.subcategory_valid, state=Form.subcategory)
async def process_subcategory(
    callback: types.CallbackQuery, state: FSMContext
) -> types.Message:
    message = callback.message
    await state.update_data(subcategory=callback.data)
    state_data = await parse_state(state=state)
    await state.set_state(Form.course)
    return await dispatcher.send_course_message(
        message=message,
        category=state_data.category,
        subcategory=state_data.subcategory,
    )


@dispatcher.dp.callback_query_handler(
    filters.subcategory_invalid, state=Form.subcategory
)
async def process_subcategory_invalid(message: types.Message, state: FSMContext):
    data = await parse_state(state=state)
    return await send_message(
        dispatcher.bot,
        chat_id=message.chat.id,
        text=messages.SUBCATEGORY_WRONG,
        reply_markup=get_keyboard_markup(
            buttons=sorted(database.subcategories[data.category])
        ),
    )
