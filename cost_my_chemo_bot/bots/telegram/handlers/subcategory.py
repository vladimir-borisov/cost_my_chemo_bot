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


@dispatcher.dp.callback_query_handler(filters.nosology_valid, state=Form.nosology)
async def process_nosology(
    callback: types.CallbackQuery, state: FSMContext
) -> types.Message:
    message = callback.message
    await state.update_data(nosology=callback.data)
    state_data = await parse_state(state=state)
    await state.set_state(Form.course)
    return await dispatcher.send_course_message(
        message=message,
        category_id=state_data.category_id,
        nosology_id=state_data.nosology_id,
    )


@dispatcher.dp.callback_query_handler(filters.nosology_invalid, state=Form.nosology)
async def process_nosology_invalid(message: types.Message, state: FSMContext):
    data = await parse_state(state=state)
    return await send_message(
        dispatcher.bot,
        chat_id=message.chat.id,
        text=messages.NOSOLOGY_WRONG,
        reply_markup=get_keyboard_markup(
            buttons=sorted(database.nosologies[data.category_id])
        ),
    )
