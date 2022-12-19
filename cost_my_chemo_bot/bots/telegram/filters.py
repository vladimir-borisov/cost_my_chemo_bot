from aiogram import Dispatcher, types
from aiogram.dispatcher.filters import Command, Text

from cost_my_chemo_bot.bots.telegram.state import parse_state
from cost_my_chemo_bot.db import DB

database = DB()


welcome_callback = Text(equals=["start", "help", "menu"], ignore_case=True)
welcome_message = Command(commands=["start", "help", "menu"])
welcome_message_text = Text(equals=["start", "help", "menu"], ignore_case=True)
back_valid = Text(equals="back", ignore_case=True)


async def height_valid(message: types.Message) -> bool:
    return message.text.isdigit()


async def height_invalid(message: types.Message) -> bool:
    return not message.text.isdigit()


async def weight_valid(message: types.Message) -> bool:
    return message.text.isdigit()


async def weight_invalid(message: types.Message) -> bool:
    return not message.text.isdigit()


async def category_invalid(callback: types.CallbackQuery) -> bool:
    return callback.data not in database.categories


async def subcategory_valid(callback: types.CallbackQuery) -> bool:
    message = callback.message
    dp = Dispatcher.get_current()
    state = dp.current_state(user=callback.from_user.id, chat=message.chat.id)
    state_data = await parse_state(state=state)
    return callback.data in database.subcategories[state_data.category]


async def subcategory_invalid(callback: types.CallbackQuery) -> bool:
    dp = Dispatcher.get_current()
    message = callback.message
    state = dp.current_state(chat=message.chat.id, user=message.from_user.id)
    data = await parse_state(state=state)
    return message.text not in database.subcategories[data.category]


async def course_valid(callback: types.CallbackQuery) -> bool:
    message = callback.message
    dp = Dispatcher.get_current()
    state = dp.current_state(user=callback.from_user.id, chat=message.chat.id)
    state_data = await parse_state(state=state)
    filtered_courses = await database.find_courses(
        category=state_data.category,
        subcategory=state_data.subcategory,
    )
    try:
        course_id = int(callback.data)
    except ValueError:
        return False

    filtered_courses = [course for course in filtered_courses if course.id == course_id]
    if not filtered_courses:
        return False

    assert len(filtered_courses) == 1
    return True


async def course_invalid(callback: types.CallbackQuery) -> bool:
    message = callback.message
    dp = Dispatcher.get_current()
    state = dp.current_state(chat=message.chat.id, user=callback.from_user.id)
    data = await parse_state(state=state)
    filtered_courses = await database.find_courses(
        category=data.category, subcategory=data.subcategory
    )

    try:
        course_id = int(callback.data)
    except ValueError:
        return True

    filtered_courses = [course for course in filtered_courses if course.id == course_id]
    if not filtered_courses:
        return True

    assert len(filtered_courses) == 1
    return False
