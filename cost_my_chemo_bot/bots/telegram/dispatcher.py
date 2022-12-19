import logging

import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.files import JSONStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.webhook import SendMessage
from aiogram.types import ParseMode

from cost_my_chemo_bot.bots.telegram import messages
from cost_my_chemo_bot.bots.telegram.keyboard import get_keyboard_markup
from cost_my_chemo_bot.bots.telegram.send import send_message
from cost_my_chemo_bot.bots.telegram.state import parse_state
from cost_my_chemo_bot.config import SETTINGS
from cost_my_chemo_bot.db import DB

logger = logging.getLogger(__name__)

bot = Bot(token=SETTINGS.TELEGRAM_BOT_TOKEN)
storage = JSONStorage(SETTINGS.STATE_STORAGE_PATH)
dp = Dispatcher(bot, storage=storage)
database = DB()


async def send_height_message(
    message: types.Message, initial: bool = False
) -> types.Message | SendMessage:
    text = ""
    if initial:
        text += messages.WELCOME.format(full_name=message.from_user.full_name)
    text += messages.HEIGHT_INPUT
    return await send_message(
        bot,
        chat_id=message.chat.id,
        text=text,
        reply_markup=types.ReplyKeyboardRemove(),
    )


async def send_weight_message(message: types.Message) -> types.Message | SendMessage:
    return await send_message(
        bot,
        chat_id=message.chat.id,
        text=messages.WEIGHT_INPUT,
        reply_markup=get_keyboard_markup(),
    )


async def send_category_message(message: types.Message) -> types.Message:
    return await send_message(
        bot,
        chat_id=message.chat.id,
        text=messages.CATEGORY_CHOOSE,
        reply_markup=get_keyboard_markup(buttons=sorted(database.categories)),
    )


async def send_subcategory_message(
    message: types.Message, state: FSMContext
) -> types.Message | SendMessage:
    state_data = await parse_state(state=state)
    return await send_message(
        bot,
        chat_id=message.chat.id,
        text=messages.SUBCATEGORY_CHOOSE,
        reply_markup=get_keyboard_markup(
            buttons=sorted(database.subcategories[state_data.category])
        ),
    )


async def send_course_message(
    message: types.Message, category: str, subcategory: str
) -> types.Message | SendMessage:
    recommended_courses = await database.find_courses(
        category=category, subcategory=subcategory
    )
    recommended_courses_names = sorted({course.name for course in recommended_courses})
    return await send_message(
        bot,
        chat_id=message.chat.id,
        text=messages.COURSE_CHOOSE,
        reply_markup=get_keyboard_markup(
            buttons=sorted(recommended_courses_names), index_callback=True
        ),
    )


async def send_lead_message(
    message: types.Message, add_text: str | None = None
) -> types.Message | SendMessage:
    if add_text is None:
        add_text = ""

    return await send_message(
        bot,
        chat_id=message.chat.id,
        text=md.text(add_text, md.text(messages.LEAD_SHARE), sep="\n"),
        reply_markup=get_keyboard_markup(
            buttons=[types.KeyboardButton(text="Share", request_contact=True)],
            inline=False,
        ),
        parse_mode=ParseMode.MARKDOWN,
    )
