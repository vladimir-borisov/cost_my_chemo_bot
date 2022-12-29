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
from cost_my_chemo_bot.db import DB, Course

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
        text += messages.WELCOME.format(full_name=message.chat.full_name)
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
    buttons = []
    for category in sorted(database.categories, key=lambda item: item.categoryName):
        buttons.append(
            types.InlineKeyboardButton(
                text=category.categoryName,
                callback_data=category.categoryid,
            )
        )
    return await send_message(
        bot,
        chat_id=message.chat.id,
        text=messages.CATEGORY_CHOOSE,
        reply_markup=get_keyboard_markup(buttons=buttons),
    )


async def send_nosology_message(
    message: types.Message, state: FSMContext
) -> types.Message | SendMessage:
    buttons = []
    for nosology in sorted(database.nosologies, key=lambda item: item.nosologyName):
        buttons.append(
            types.InlineKeyboardButton(
                text=nosology.nosologyName,
                callback_data=nosology.nosologyid,
            )
        )
    return await send_message(
        bot,
        chat_id=message.chat.id,
        text=messages.NOSOLOGY_CHOOSE,
        reply_markup=get_keyboard_markup(buttons=buttons),
    )


async def send_course_message(
    message: types.Message, category_id: str, nosology_id: str
) -> types.Message | SendMessage:
    recommended_courses: list[Course] = await database.find_courses(
        category_id=category_id, nosology_id=nosology_id
    )
    logger.info(
        "category_id=%s nosology_id=%s recommended_courses=%s",
        category_id,
        nosology_id,
        recommended_courses,
    )
    buttons = []
    for course in sorted(recommended_courses, key=lambda item: item.Course):
        buttons.append(
            types.InlineKeyboardButton(
                text=course.Course,
                callback_data=course.Courseid,
            )
        )

    return await send_message(
        bot,
        chat_id=message.chat.id,
        text=messages.COURSE_CHOOSE,
        reply_markup=get_keyboard_markup(buttons=buttons),
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
