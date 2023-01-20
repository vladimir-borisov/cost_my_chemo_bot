import decimal

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.webhook import SendMessage
from logfmt_logger import getLogger

from cost_my_chemo_bot.bots.telegram import dispatcher, filters, messages
from cost_my_chemo_bot.bots.telegram.keyboard import get_keyboard_markup
from cost_my_chemo_bot.bots.telegram.messages import course_selected
from cost_my_chemo_bot.bots.telegram.send import send_message
from cost_my_chemo_bot.bots.telegram.state import Form, parse_state
from cost_my_chemo_bot.db import DB

logger = getLogger(__name__)
database = DB()


async def calculate_course_price(course_id: str, bsa: float) -> decimal.Decimal:
    course = await database.find_course_by_id(course_id=course_id)
    return course.price(bsa=bsa)


@dispatcher.dp.callback_query_handler(filters.course_valid, state=Form.course)
async def process_course(
    callback: types.CallbackQuery, state: FSMContext
) -> types.Message | SendMessage:
    message = callback.message
    await state.update_data(course_id=callback.data)
    state_data = await parse_state(state=state)
    course_price = await calculate_course_price(
        course_id=state_data.course_id,
        bsa=state_data.bsa,
    )
    category = await database.find_category_by_id(category_id=state_data.category_id)
    nosology = await database.find_nosology_by_id(nosology_id=state_data.nosology_id)
    course = await database.find_course_by_id(course_id=state_data.course_id)
    course_text = course_selected(
        height=state_data.height,
        weight=state_data.weight,
        category=category,
        nosology=nosology,
        course=course,
        course_price=course_price,
    )
    await state.set_state(Form.first_name)
    return await dispatcher.send_first_name_message(message=message, add_text=course_text)


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
