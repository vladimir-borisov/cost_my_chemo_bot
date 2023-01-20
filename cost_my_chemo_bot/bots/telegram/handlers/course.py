from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.webhook import SendMessage
from logfmt_logger import getLogger

from cost_my_chemo_bot.bots.telegram import dispatcher, filters, messages
from cost_my_chemo_bot.bots.telegram.keyboard import get_keyboard_markup
from cost_my_chemo_bot.bots.telegram.send import send_message
from cost_my_chemo_bot.bots.telegram.state import Form, parse_state
from cost_my_chemo_bot.db import DB

logger = getLogger(__name__)
database = DB()


@dispatcher.dp.callback_query_handler(filters.course_valid, state=Form.course)
async def process_course(
    callback: types.CallbackQuery, state: FSMContext
) -> types.Message | SendMessage:
    message = callback.message
    await state.update_data(course_id=callback.data)
    await state.set_state(Form.data_confirmation)
    return await dispatcher.send_data_confirmation_message(message=message, state=state)


@dispatcher.dp.callback_query_handler(filters.course_invalid, state=Form.course)
async def process_course_invalid(callback: types.CallbackQuery, state: FSMContext):
    message = callback.message
    data = await parse_state(state=state)
    courses = await database.find_courses(
        category_id=data.category_id, nosology_id=data.nosology_id
    )
    return await send_message(
        dispatcher.bot,
        chat_id=message.chat.id,
        text=messages.COURSE_WRONG,
        reply_markup=get_keyboard_markup(
            buttons=sorted([course.Course for course in courses])
        ),
    )


async def process_data_confirmation(
    callback: types.CallbackQuery, state: FSMContext
) -> types.Message | SendMessage:
    message = callback.message
    await state.update_data(data_confirmation=message.text)
    await state.set_state(Form.contacts_input)
    return await dispatcher.send_contacts_input_message(message=message, state=state)


async def process_data_reenter(callback: types.CallbackQuery, state: FSMContext):
    message = callback.message
    await state.set_state(Form.height)
    return await dispatcher.send_height_message(message=message)


def init_course_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(
        process_data_confirmation, filters.data_confirmed, state=Form.data_confirmation
    )
    dp.register_callback_query_handler(
        process_data_reenter, filters.data_reenter, state=Form.data_confirmation
    )
