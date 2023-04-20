from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.webhook import SendMessage
from logfmt_logger import getLogger

from cost_my_chemo_bot.bots.telegram import dispatcher, filters, messages
from cost_my_chemo_bot.bots.telegram.keyboard import Buttons, get_keyboard_markup
from cost_my_chemo_bot.bots.telegram.send import send_message
from cost_my_chemo_bot.bots.telegram.state import Form, parse_state
from cost_my_chemo_bot.db import DB
from cost_my_chemo_bot.action_logger.main import action_logger

logger = getLogger(__name__)
database = DB()


async def process_course(
    callback: types.CallbackQuery, state: FSMContext
) -> types.Message | SendMessage:

    message = callback.message

    course_object = await database.find_course_by_id(course_id=callback.data)
    course_name = course_object.Course

    await action_logger.send_message(message=f"Пользователь выбрал курс: '{course_name}'",
                                     user_id=message.chat.id,
                                     username=f"{message.chat.first_name} {message.chat.last_name}")

    await state.update_data(
        course_id=course_object.Courseid,
        course_name=course_name,
    )


    await state.set_state(Form.data_confirmation)
    return await dispatcher.send_data_confirmation_message(message=message, state=state)


async def process_course_invalid(callback: types.CallbackQuery, state: FSMContext):
    bot = Bot.get_current()

    message = callback.message
    data = await parse_state(state=state)
    courses = await database.find_courses(
        category_id=data.category_id, nosology_id=data.nosology_id
    )
    return await send_message(
        bot,
        chat_id=message.chat.id,
        text=messages.COURSE_WRONG,
        reply_markup=get_keyboard_markup(
            buttons=sorted(
                [course.Course for course in courses], [Buttons.CUSTOM_COURSE.value]
            )
        ),
    )


async def process_enter_custom_course(callback: types.CallbackQuery, state: FSMContext):
    message = callback.message
    await state.update_data(is_custom_course=True)
    await state.set_state(Form.custom_course)
    return await dispatcher.send_custom_course_message(message=message)


async def process_custom_course(
    message: types.Message, state: FSMContext
) -> types.Message | SendMessage:

    await action_logger.send_message(message=f"Пользователь ввел собственный курс: '{message.text}'",
                                     user_id=message.chat.id,
                                     username=f"{message.chat.first_name} {message.chat.last_name}")

    await state.update_data(course_name=message.text)
    await state.set_state(Form.data_confirmation)
    return await dispatcher.send_data_confirmation_message(message=message, state=state)


async def process_data_confirmation(
    callback: types.CallbackQuery, state: FSMContext
) -> types.Message | SendMessage:

    message = callback.message

    await action_logger.send_message(message=f"Показываем пользователю все выбранные и введенные данные",
                                     user_id=message.chat.id,
                                     username=f"{message.chat.first_name} {message.chat.last_name}")

    await state.update_data(data_confirmation=message.text)
    await state.set_state(Form.contacts_input)
    return await dispatcher.send_contacts_input_message(message=message, state=state)


async def process_data_reenter(callback: types.CallbackQuery, state: FSMContext):
    message = callback.message

    await action_logger.send_message(message=f"Пользователь решил исправить введенные данные",
                                     user_id=message.chat.id,
                                     username=f"{message.chat.first_name} {message.chat.last_name}")

    await state.set_state(Form.height)
    return await dispatcher.send_height_message(message=message)


def init_course_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(
        process_course, filters.course_valid, state=Form.course
    )
    dp.register_callback_query_handler(
        process_course_invalid, filters.course_invalid, state=Form.course
    )

    dp.register_callback_query_handler(
        process_enter_custom_course, filters.enter_custom_course, state=Form.course
    )
    dp.register_message_handler(process_custom_course, state=Form.custom_course)

    dp.register_callback_query_handler(
        process_data_confirmation, filters.data_confirmed, state=Form.data_confirmation
    )
    dp.register_callback_query_handler(
        process_data_reenter, filters.data_reenter, state=Form.data_confirmation
    )
