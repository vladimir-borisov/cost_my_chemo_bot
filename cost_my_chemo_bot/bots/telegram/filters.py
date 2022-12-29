from aiogram import Dispatcher, types
from aiogram.dispatcher.filters import Command, Text

from cost_my_chemo_bot.bots.telegram.state import parse_state
from cost_my_chemo_bot.db import DB

database = DB()


welcome_callback = Text(equals=["start", "menu"], ignore_case=True)
welcome_message = Command(commands=["start", "menu"])
welcome_message_text = Text(equals=["start", "menu"], ignore_case=True)
back_valid = Text(equals="back", ignore_case=True)


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
    if callback.data in ("menu", "back"):
        return False
    return bool(
        [
            category
            for category in database.categories
            if callback.data == category.categoryid
        ]
    )


async def nosology_valid(callback: types.CallbackQuery) -> bool:
    nosology_id = callback.data
    return bool(
        [
            nosology
            for nosology in database.nosologies
            if nosology.nosologyid == nosology_id
        ]
    )


async def nosology_invalid(callback: types.CallbackQuery) -> bool:
    if callback.data in ("menu", "back"):
        return False
    nosology_id = callback.data
    return bool(
        [
            nosology
            for nosology in database.nosologies
            if nosology.nosologyid == nosology_id
        ]
    )


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
    filtered_courses = [
        course for course in filtered_courses if course.Courseid == course_id
    ]
    if not filtered_courses:
        return False

    assert len(filtered_courses) == 1
    return True


async def course_invalid(callback: types.CallbackQuery) -> bool:
    if callback.data in ("menu", "back"):
        return False

    message = callback.message
    dp = Dispatcher.get_current()
    state = dp.current_state(chat=message.chat.id, user=callback.from_user.id)
    data = await parse_state(state=state)
    filtered_courses = await database.find_courses(
        category_id=data.category_id, nosology_id=data.nosology_id
    )

    course_id = callback.data
    filtered_courses = [
        course for course in filtered_courses if course.Courseid == course_id
    ]
    if not filtered_courses:
        return True

    assert len(filtered_courses) == 1
    return False
