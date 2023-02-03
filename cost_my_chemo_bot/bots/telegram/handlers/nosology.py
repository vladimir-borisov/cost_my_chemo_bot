from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from logfmt_logger import getLogger

from cost_my_chemo_bot.bots.telegram import dispatcher, filters, messages
from cost_my_chemo_bot.bots.telegram.keyboard import get_keyboard_markup
from cost_my_chemo_bot.bots.telegram.send import send_message
from cost_my_chemo_bot.bots.telegram.state import Form, parse_state
from cost_my_chemo_bot.db import DB

logger = getLogger(__name__)
database = DB()


async def process_nosology(
    callback: types.CallbackQuery, state: FSMContext
) -> types.Message:
    message = callback.message
    await state.update_data(nosology_id=callback.data)
    state_data = await parse_state(state=state)
    await state.set_state(Form.course)
    return await dispatcher.send_course_message(
        message=message,
        category_id=state_data.category_id,
        nosology_id=state_data.nosology_id,
    )


async def process_nosology_invalid(message: types.Message, state: FSMContext):
    buttons = []
    data = await parse_state(state=state)
    nosologies = await database.find_nosologies_by_category_id(
        category_id=data.category_id
    )
    for nosology in sorted(nosologies, key=lambda item: item.nosologyName):
        buttons.append(
            types.InlineKeyboardButton(
                text=nosology.nosologyName,
                callback_data=nosology.nosologyid,
            )
        )
    return await send_message(
        dispatcher.bot,
        chat_id=message.chat.id,
        text=messages.NOSOLOGY_WRONG,
        reply_markup=get_keyboard_markup(buttons=buttons),
    )


def init_nosology_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(
        process_nosology, filters.nosology_valid, state=Form.nosology
    )

    dp.register_callback_query_handler(
        process_nosology_invalid, filters.nosology_invalid, state=Form.nosology
    )
