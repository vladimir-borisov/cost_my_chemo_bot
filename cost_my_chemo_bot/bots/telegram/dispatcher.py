import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.files import JSONStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.webhook import SendMessage
from aiogram.types import ParseMode
from aiogram.utils.text_decorations import HtmlDecoration
from logfmt_logger import getLogger

from cost_my_chemo_bot.bots.telegram import messages
from cost_my_chemo_bot.bots.telegram.keyboard import Buttons, get_keyboard_markup
from cost_my_chemo_bot.bots.telegram.send import send_message
from cost_my_chemo_bot.bots.telegram.state import parse_state
from cost_my_chemo_bot.bots.telegram.storage import GcloudStorage
from cost_my_chemo_bot.config import JSON_STORAGE_SETTINGS, SETTINGS, StorageType
from cost_my_chemo_bot.db import DB, Course

logger = getLogger(__name__)

bot = Bot(token=SETTINGS.TELEGRAM_BOT_TOKEN)
if SETTINGS.STORAGE_TYPE is StorageType.JSON:
    storage = JSONStorage(JSON_STORAGE_SETTINGS.STATE_STORAGE_PATH)
elif SETTINGS.STORAGE_TYPE is StorageType.GCLOUD:
    storage = GcloudStorage()
# storage = FirestoreStorage()
dp = Dispatcher(bot, storage=storage)
database = DB()


async def send_welcome_message(
    message: types.Message, initial: bool = False
) -> types.Message | SendMessage:
    text = ""
    if initial:
        text += messages.WELCOME

    kb = types.InlineKeyboardMarkup()
    kb.add(Buttons.YES.value)
    return await send_message(
        bot,
        chat_id=message.chat.id,
        text=text,
        reply_markup=kb,
    )


async def send_height_message(message: types.Message) -> types.Message | SendMessage:
    text = messages.HEIGHT_INPUT
    return await send_message(
        bot,
        chat_id=message.chat.id,
        text=text,
        reply_markup=get_keyboard_markup(),
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
        bot,
        chat_id=message.chat.id,
        text=messages.NOSOLOGY_CHOOSE,
        reply_markup=get_keyboard_markup(buttons=buttons),
    )


async def send_course_message(
    message: types.Message, category_id: str, nosology_id: str | None
) -> types.Message | SendMessage:
    recommended_courses: list[Course] = await database.find_courses(
        category_id=category_id, nosology_id=nosology_id
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


async def send_data_confirmation_message(
    message: types.Message, state: FSMContext
) -> types.Message | SendMessage:
    state_data = await parse_state(state=state)
    category = await database.find_category_by_id(category_id=state_data.category_id)
    nosology = ""
    if not state_data.is_accompanying_therapy:
        nosology = await database.find_nosology_by_id(
            nosology_id=state_data.nosology_id
        )
    course = await database.find_course_by_id(course_id=state_data.course_id)
    html_decoration = HtmlDecoration()
    return await send_message(
        bot,
        chat_id=message.chat.id,
        text=messages.DATA_CONFIRMATION.format(
            height=html_decoration.bold(state_data.height),
            weight=html_decoration.bold(state_data.weight),
            category_name=html_decoration.bold(category.categoryName),
            nosology_name=html_decoration.bold(
                nosology.nosologyName if nosology else ""
            ),
            course_name=html_decoration.bold(course.Course),
        ),
        reply_markup=get_keyboard_markup(
            buttons=[Buttons.YES.value, Buttons.NEED_CORRECTION.value]
        ),
        parse_mode=ParseMode.HTML,
    )


async def send_contacts_input_message(
    message: types.Message, state: FSMContext
) -> types.Message | SendMessage:
    state_data = await parse_state(state=state)
    category = await database.find_category_by_id(category_id=state_data.category_id)
    nosology = ""
    if not state_data.is_accompanying_therapy:
        nosology = await database.find_nosology_by_id(
            nosology_id=state_data.nosology_id
        )
    course = await database.find_course_by_id(course_id=state_data.course_id)
    course_price = course.price(bsa=state_data.bsa)
    html_decoration = HtmlDecoration()
    return await send_message(
        bot,
        chat_id=message.chat.id,
        text=messages.DATA_CORRECT.format(
            height=html_decoration.bold(state_data.height),
            weight=html_decoration.bold(state_data.weight),
            category_name=html_decoration.bold(category.categoryName),
            nosology_name=html_decoration.bold(
                nosology.nosologyName if nosology else ""
            ),
            course_name=html_decoration.bold(course.Course),
            course_price=html_decoration.bold(f"{course_price:.2f}"),
        ),
        reply_markup=get_keyboard_markup(buttons=[Buttons.CONTACTS_INPUT.value]),
        parse_mode=ParseMode.HTML,
    )


async def send_first_name_message(
    message: types.Message, add_text: str | None = None
) -> types.Message | SendMessage:
    if add_text is None:
        add_text = ""
    text = md.text(add_text, md.text(messages.LEAD_FIRST_NAME), sep="\n")
    return await send_message(
        bot,
        chat_id=message.chat.id,
        text=text,
        reply_markup=get_keyboard_markup(buttons=[Buttons.SKIP.value]),
        parse_mode=ParseMode.MARKDOWN,
    )


async def send_last_name_message(
    message: types.Message,
) -> types.Message | SendMessage:
    text = messages.LEAD_LAST_NAME
    return await send_message(
        bot,
        chat_id=message.chat.id,
        text=text,
        reply_markup=get_keyboard_markup(buttons=[Buttons.SKIP.value]),
    )


async def send_email_message(
    message: types.Message,
) -> types.Message | SendMessage:
    text = messages.LEAD_EMAIL
    return await send_message(
        bot,
        chat_id=message.chat.id,
        text=text,
        reply_markup=get_keyboard_markup(buttons=[Buttons.SKIP.value]),
    )


async def send_email_invalid_message(
    message: types.Message,
) -> types.Message | SendMessage:
    text = messages.LEAD_EMAIL_WRONG
    return await send_message(
        bot,
        chat_id=message.chat.id,
        text=text,
        reply_markup=get_keyboard_markup(),
    )


async def send_phone_number_message(
    message: types.Message,
) -> types.Message | SendMessage:
    text = messages.LEAD_PHONE_NUMBER
    return await send_message(
        bot,
        chat_id=message.chat.id,
        text=text,
        reply_markup=get_keyboard_markup(buttons=[Buttons.SKIP.value]),
    )


async def send_phone_number_invalid_message(
    message: types.Message,
) -> types.Message | SendMessage:
    text = messages.LEAD_PHONE_NUMBER_WRONG
    return await send_message(
        bot,
        chat_id=message.chat.id,
        text=text,
        reply_markup=get_keyboard_markup(),
    )


async def send_lead_confirmation_message(
    message: types.Message, state: FSMContext
) -> types.Message | SendMessage:
    state_data = await parse_state(state=state)
    html_decoration = HtmlDecoration()
    return await send_message(
        bot,
        chat_id=message.chat.id,
        text=messages.LEAD_CONFIRMATION.format(
            first_name=html_decoration.bold(state_data.first_name or ""),
            last_name=html_decoration.bold(state_data.last_name or ""),
            email=html_decoration.bold(state_data.email or ""),
            phone_number=html_decoration.bold(state_data.phone_number or ""),
        ),
        reply_markup=get_keyboard_markup(
            buttons=[Buttons.YES.value, Buttons.NEED_CORRECTION.value]
        ),
        parse_mode=ParseMode.HTML,
    )


async def send_final_message(
    message: types.Message,
) -> types.Message | SendMessage:
    return await send_message(
        bot,
        chat_id=message.chat.id,
        text=messages.FINAL_MESSAGE,
        reply_markup=get_keyboard_markup(),
    )
