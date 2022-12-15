import decimal
import logging
import math

import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.files import JSONStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode
from aiogram.dispatcher.webhook import SendMessage
from pydantic import BaseModel


from cost_my_chemo_bot.bots.telegram.keyboard import get_keyboard_markup
from cost_my_chemo_bot.config import SETTINGS
from cost_my_chemo_bot.db import DB
from cost_my_chemo_bot.bots.telegram.send import send_message

logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
bot = Bot(token=SETTINGS.TELEGRAM_BOT_TOKEN)
storage = JSONStorage("storage.json")
dp = Dispatcher(bot, storage=storage)
database = DB()


class StateData(BaseModel):
    height: int | None = None
    weight: int | None = None
    category: str | None = None
    subcategory: str | None = None
    course: str | None = None

    @property
    def bsa(self) -> float:
        assert self.height is not None and self.weight is not None
        return math.sqrt(self.height * self.weight / 3600)


# States
class Form(StatesGroup):
    height = State()
    weight = State()
    category = State()
    subcategory = State()
    course = State()
    lead = State()


async def parse_state(state: FSMContext) -> StateData:
    data = await state.get_data()
    return StateData(**data)


async def course_filter(message: types.Message) -> bool:
    state = dp.current_state(chat=message.chat.id, user=message.from_user.id)
    state_data = await parse_state(state=state)
    filtered_courses = await database.find_courses(
        category=state_data.category,
        subcategory=state_data.subcategory,
    )
    return message.text in [course["название курса"] for course in filtered_courses]


async def subcategory_filter(message: types.Message) -> bool:
    state = dp.current_state(chat=message.chat.id, user=message.from_user.id)
    state_data = await parse_state(state=state)
    return message.text in database.subcategories[state_data.category]


async def send_height_message(
    message: types.Message, initial: bool = False
) -> types.Message | SendMessage:
    text = ""
    if initial:
        text += (
            f"Здравствуйте, {message.from_user.full_name}!\n"
            "Я помогу рассчитать стоимость курса лечения"
        )
    text += "Введите ваш рост"
    return await send_message(
        bot,
        chat_id=message.chat.id,
        text=text,
        reply_markup=types.ReplyKeyboardRemove(),
    )


@dp.message_handler(commands=["start", "help", "menu"], state="*")
@dp.message_handler(Text(equals=["start", "help", "menu"], ignore_case=True), state="*")
async def send_welcome(
    message: types.Message, state: FSMContext
) -> types.Message | SendMessage:
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    logger.info(
        "all_states: %s, all_states_names: %s", Form.all_states, Form.all_states_names
    )
    current_state = await state.get_state()
    if current_state is not None:
        logger.info("Cancelling state %r", current_state)
        await state.finish()

    await state.set_state(Form.height)
    return await send_height_message(message=message, initial=True)


@dp.message_handler(state="*", commands=["cancel", "stop"])
@dp.message_handler(Text(equals="cancel", ignore_case=True), state="*")
@dp.message_handler(Text(equals="stop", ignore_case=True), state="*")
async def cancel_handler(
    message: types.Message, state: FSMContext
) -> types.Message | SendMessage:
    """
    Allow user to cancel any action
    """
    current_state = await state.get_state()
    if current_state is None:
        return

    logger.info("Cancelling state %r", current_state)
    await state.finish()
    return await send_message(
        bot,
        chat_id=message.chat.id,
        text="Cancelled.",
        reply_markup=types.ReplyKeyboardRemove(),
    )


@dp.message_handler(state="*", commands="back")
@dp.message_handler(Text(equals="back", ignore_case=True), state="*")
async def back_handler(
    message: types.Message, state: FSMContext
) -> types.Message | SendMessage:
    current_state = await state.get_state()
    logger.debug("back from state: %s", current_state)
    if current_state is None:
        await Form.last()
        current_state = await Form.previous()
    else:
        current_state = await Form.previous()
    logger.debug("current state: %s", current_state)
    state_data = await parse_state(state=state)
    logger.debug("state data: %s", state_data)
    try:
        match current_state:
            case Form.height.state:
                return await send_height_message(message=message)
            case Form.weight.state:
                return await send_weight_message(message=message)
            case Form.category.state:
                return await send_category_message(message=message)
            case Form.subcategory.state:
                return await send_subcategory_message(
                    message=message,
                    state=state,
                )
            case Form.course.state:
                return await send_course_message(
                    message=message,
                    category=state_data.category,
                    subcategory=state_data.subcategory,
                )
            case Form.lead.state:
                return await send_lead_message(message=message)
    finally:
        await message.delete()


async def send_weight_message(message: types.Message) -> types.Message | SendMessage:
    return await send_message(
        bot,
        chat_id=message.chat.id,
        text="Введите ваш вес",
        reply_markup=get_keyboard_markup(),
    )


@dp.message_handler(lambda message: message.text.isdigit(), state=Form.height)
async def process_height(message: types.Message, state: FSMContext) -> types.Message | SendMessage:
    await state.update_data(height=int(message.text))
    await state.set_state(Form.weight)
    return await send_weight_message(message=message)


async def send_category_message(message: types.Message) -> types.Message:
    return await send_message(
        bot,
        chat_id=message.chat.id,
        text="Выберите раздел",
        reply_markup=get_keyboard_markup(buttons=sorted(database.categories)),
    )


@dp.message_handler(lambda message: message.text.isdigit(), state=Form.weight)
async def process_weight(message: types.Message, state: FSMContext) -> types.Message | SendMessage:
    await state.update_data(weight=int(message.text))
    await state.set_state(Form.category)
    return await send_category_message(message=message)


async def send_subcategory_message(
    message: types.Message, state: FSMContext
) -> types.Message | SendMessage:
    state_data = await parse_state(state=state)
    return await send_message(
        bot,
        chat_id=message.chat.id,
        text="Выберите подраздел",
        reply_markup=get_keyboard_markup(
            buttons=sorted(database.subcategories[state_data.category])
        ),
    )


@dp.message_handler(
    lambda message: message.text in database.categories, state=Form.category
)
async def process_category(message: types.Message, state: FSMContext) -> types.Message | SendMessage:
    await state.update_data(category=message.text)
    await state.set_state(Form.subcategory)
    return await send_subcategory_message(message=message, state=state)


async def send_course_message(
    message: types.Message, category: str, subcategory: str
) -> types.Message | SendMessage:
    recommended_courses = await database.find_courses(
        category=category, subcategory=subcategory
    )
    return await send_message(
        bot,
        chat_id=message.chat.id,
        text="Выберите курс",
        reply_markup=get_keyboard_markup(
            buttons=sorted([course["название курса"] for course in recommended_courses])
        ),
    )


@dp.message_handler(subcategory_filter, state=Form.subcategory)
async def process_subcategory(
    message: types.Message, state: FSMContext
) -> types.Message:
    await state.update_data(subcategory=message.text)
    state_data = await parse_state(state=state)
    await state.set_state(Form.course)
    return await send_course_message(
        message=message,
        category=state_data.category,
        subcategory=state_data.subcategory,
    )


async def calculate_course_price(course_name: str, bsa: float) -> decimal.Decimal:
    course: dict[str, str] = await database.find_course_by_name(name=course_name)
    return (
        decimal.Decimal(course["коэффициент"].replace(" ", "").replace(",", "."))
        * decimal.Decimal(str(bsa))
        * decimal.Decimal("0.6")
    )


async def send_lead_message(message: types.Message) -> types.Message | SendMessage:
    return await send_message(
        bot,
        chat_id=message.chat.id,
        text="Введите номер телефона для связи",
        reply_markup=get_keyboard_markup(
            buttons=[types.KeyboardButton(text="Share", request_contact=True)]
        ),
    )


@dp.message_handler(course_filter, state=Form.course)
async def process_course(message: types.Message, state: FSMContext) -> types.Message:
    await state.update_data(course=message.text)
    state_data = await parse_state(state=state)
    course_price = await calculate_course_price(
        course_name=state_data.course,
        bsa=state_data.bsa,
    )

    await send_message(
        bot,
        chat_id=message.chat.id,
        text=md.text(
            md.text("Рост:", md.bold(state_data.height)),
            md.text("Вес:", md.code(state_data.weight)),
            md.text("Категория:", md.italic(state_data.category)),
            md.text("Подкатегория:", md.italic(state_data.subcategory)),
            md.text("Курс:", state_data.course),
            md.text("Цена:", f"{course_price:.2f}".replace(".", ",")),
            sep="\n",
        ),
        reply_markup=get_keyboard_markup(),
        parse_mode=ParseMode.MARKDOWN,
    )
    await state.set_state(Form.lead)
    return await send_lead_message(message=message)


@dp.message_handler(state=Form.lead, content_types=types.ContentType.CONTACT)
async def process_lead(message: types.Message, state: FSMContext):
    logger.info("%s", message.contact)
    await state.update_data(lead=message.contact.as_json())
    await state.set_state(None)


@dp.message_handler(
    lambda message: message.text not in database.categories,
    state=Form.category,
)
async def process_category_invalid(message: types.Message) -> types.Message | SendMessage:
    return await send_message(
        bot,
        chat_id=message.chat.id,
        text="Неверно выбрана категория. Выберите категорию на клавиатуре.",
        reply_markup=get_keyboard_markup(buttons=sorted(database.categories)),
    )


async def invalid_subcategory_filter(message: types.Message) -> bool:
    state = dp.current_state(chat=message.chat.id, user=message.from_user.id)
    data = await state.get_data()
    category = data["category"]
    return message.text not in database.subcategories[category]


@dp.message_handler(
    invalid_subcategory_filter,
    state=Form.subcategory,
)
async def process_subcategory_invalid(message: types.Message, state: FSMContext):
    data = await state.get_data()
    category = data["category"]
    return await send_message(
        bot,
        chat_id=message.chat.id,
        text="Неверно выбрана подкатегория. Выберите подкатегорию на клавиатуре.",
        reply_markup=get_keyboard_markup(
            buttons=sorted(database.subcategories[category])
        ),
    )


async def invalid_course_filter(message: types.Message) -> bool:
    state = dp.current_state(chat=message.chat.id, user=message.from_user.id)
    data = await state.get_data()
    category = data["category"]
    subcategory = data["subcategory"]

    courses = await database.find_courses(category=category, subcategory=subcategory)
    return message.text not in [course["название курса"] for course in courses]


@dp.message_handler(
    invalid_course_filter,
    state=Form.course,
)
async def process_course_invalid(message: types.Message, state: FSMContext):
    data = await state.get_data()
    category = data["category"]
    subcategory = data["subcategory"]

    courses = await database.find_courses(category=category, subcategory=subcategory)
    return await send_message(
        bot,
        chat_id=message.chat.id,
        text="Неверно выбран курс. Выберите курс на клавиатуре.",
        reply_markup=get_keyboard_markup(
            buttons=sorted([course["название курса"] for course in courses])
        ),
    )


# Check height. Height gotta be digit
@dp.message_handler(lambda message: not message.text.isdigit(), state=Form.height)
async def process_height_invalid(message: types.Message):
    return await send_message(
        bot,
        chat_id=message.chat.id,
        text="Введите число",
        reply_markup=get_keyboard_markup(),
    )


# Check weight. Weight gotta be digit
@dp.message_handler(lambda message: not message.text.isdigit(), state=Form.weight)
async def process_weight_invalid(message: types.Message):
    return await send_message(
        bot,
        chat_id=message.chat.id,
        text="Введите число",
        reply_markup=get_keyboard_markup(),
    )


async def on_startup(dp):
    # insert code here to run it after start
    await database.load_db()


async def on_shutdown(dp):
    logger.warning("Shutting down...")

    # insert code here to run it before shutdown

    # Remove webhook (not acceptable in some cases)
    # await bot.delete_webhook()

    # Close DB connection (if used)
    await dp.storage.close()
    await dp.storage.wait_closed()

    logger.warning("Bye!")
