import decimal
import logging

import aiogram.utils.markdown as md
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.webhook import SendMessage

from cost_my_chemo_bot.bots.telegram import dispatcher, filters, messages
from cost_my_chemo_bot.bots.telegram.keyboard import get_keyboard_markup
from cost_my_chemo_bot.bots.telegram.send import send_message
from cost_my_chemo_bot.bots.telegram.state import Form, parse_state
from cost_my_chemo_bot.db import DB

logger = logging.getLogger(__name__)
database = DB()


async def calculate_course_price(course_name: str, bsa: float) -> decimal.Decimal:
    course = await database.find_course_by_name(name=course_name)
    return course.price(bsa=bsa)


@dispatcher.dp.callback_query_handler(filters.course_valid, state=Form.course)
async def process_course(
    callback: types.CallbackQuery, state: FSMContext
) -> types.Message | SendMessage:
    message = callback.message
    course_name = [
        course.name for course in database.courses if course.id == int(callback.data)
    ][0]

    await state.update_data(course=course_name)
    state_data = await parse_state(state=state)
    course_price = await calculate_course_price(
        course_name=state_data.course,
        bsa=state_data.bsa,
    )

    course_text = md.text(
        md.text("Рост:", md.bold(state_data.height)),
        md.text("Вес:", md.code(state_data.weight)),
        md.text("Категория:", md.italic(state_data.category)),
        md.text("Подкатегория:", md.italic(state_data.subcategory)),
        md.text("Курс:", state_data.course),
        md.text("Цена:", f"{course_price:.2f}".replace(".", ",")),
        sep="\n",
    )
    await state.set_state(Form.lead)
    return await dispatcher.send_lead_message(message=message, add_text=course_text)


@dispatcher.dp.callback_query_handler(
    filters.course_invalid,
    state=Form.course,
)
async def process_course_invalid(callback: types.CallbackQuery, state: FSMContext):
    message = callback.message
    data = await parse_state(state=state)

    courses = await database.find_courses(
        category=data.category, subcategory=data.subcategory
    )
    return await send_message(
        dispatcher.bot,
        chat_id=message.chat.id,
        text=messages.COURSE_WRONG,
        reply_markup=get_keyboard_markup(
            buttons=sorted([course.name for course in courses])
        ),
    )
