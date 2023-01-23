from aiogram import Dispatcher, types
from aiogram.dispatcher.filters import Command, Text
from logfmt_logger import getLogger
from pydantic import EmailError, EmailStr

from cost_my_chemo_bot.bots.telegram.keyboard import Buttons
from cost_my_chemo_bot.bots.telegram.state import parse_state
from cost_my_chemo_bot.db import DB

logger = getLogger(__name__)
database = DB()


welcome_callback = Text(equals=["start", "menu"], ignore_case=True)
welcome_message = Command(commands=["start", "menu"])
welcome_message_text = Text(equals=["start", "menu"], ignore_case=True)
back_valid = Text(equals="back", ignore_case=True)


async def initial_step_confirmed(callback: types.CallbackQuery) -> bool:
    if callback.data == Buttons.YES.value.callback_data:
        return True

    return False


async def height_valid(message: types.Message) -> bool:
    if message.is_command():
        return False

    return message.text.isdigit()


async def height_invalid(message: types.Message) -> bool:
    if message.is_command():
        return False

    return not message.text.isdigit()


async def weight_valid(message: types.Message) -> bool:
    if message.is_command():
        return False

    return message.text.isdigit()


async def weight_invalid(message: types.Message) -> bool:
    if message.is_command():
        return False

    return not message.text.isdigit()


async def category_valid(callback: types.CallbackQuery) -> bool:
    return bool(
        [
            category
            for category in database.categories
            if callback.data == category.categoryid
        ]
    )


async def category_invalid(callback: types.CallbackQuery) -> bool:
    if callback.data in (
        Buttons.MENU.value.callback_data,
        Buttons.BACK.value.callback_data,
    ):
        return False

    return not await category_valid(callback=callback)


async def nosology_valid(callback: types.CallbackQuery) -> bool:
    nosology_id = callback.data
    message = callback.message
    dp = Dispatcher.get_current(no_error=False)
    state = dp.current_state(chat=message.chat.id, user=callback.from_user.id)
    data = await parse_state(state=state)
    nosologies = await database.find_nosologies_by_category_id(
        category_id=data.category_id
    )
    return bool(
        [nosology for nosology in nosologies if nosology.nosologyid == nosology_id]
    )


async def nosology_invalid(callback: types.CallbackQuery) -> bool:
    if callback.data in (
        Buttons.MENU.value.callback_data,
        Buttons.BACK.value.callback_data,
    ):
        return False

    return not await nosology_valid(callback=callback)


async def course_valid(callback: types.CallbackQuery) -> bool:
    message = callback.message
    dp = Dispatcher.get_current()
    state = dp.current_state(user=callback.from_user.id, chat=message.chat.id)
    state_data = await parse_state(state=state)
    filtered_courses = await database.find_courses(
        category_id=state_data.category_id,
        nosology_id=state_data.nosology_id,
    )
    course_id = callback.data
    course_by_id_filter = [
        course for course in filtered_courses if course.Courseid == course_id
    ]
    if not course_by_id_filter:
        return False

    assert len(course_by_id_filter) == 1
    return True


async def course_invalid(callback: types.CallbackQuery) -> bool:
    if callback.data in (
        Buttons.MENU.value.callback_data,
        Buttons.BACK.value.callback_data,
        Buttons.YES.value.callback_data,
        Buttons.NEED_CORRECTION.value.callback_data,
    ):
        return False

    return not await course_valid(callback=callback)


async def data_confirmed(callback: types.CallbackQuery) -> bool:
    return callback.data == Buttons.YES.value.callback_data


async def data_reenter(callback: types.CallbackQuery) -> bool:
    return callback.data == Buttons.NEED_CORRECTION.value.callback_data


async def contacts_input(callback: types.CallbackQuery) -> bool:
    return callback.data == Buttons.CONTACTS_INPUT.value.callback_data


async def email_valid(message: types.Message) -> bool:
    if message.is_command():
        return False

    try:
        return bool(EmailStr.validate(message.text))
    except EmailError:
        return False


async def email_invalid(message: types.Message) -> bool:
    return not await email_valid(message)


async def phone_number_valid(message: types.Message) -> bool:
    if message.is_command():
        return False

    if message.text.isdigit():
        return True

    if message.text.startswith("+"):
        return message.text[1:].isdigit()

    return False


async def phone_number_invalid(message: types.Message) -> bool:
    if message.is_command():
        return False

    return not await phone_number_valid(message)


async def skip(callback: types.CallbackQuery) -> bool:
    return callback.data == Buttons.SKIP.value.callback_data
