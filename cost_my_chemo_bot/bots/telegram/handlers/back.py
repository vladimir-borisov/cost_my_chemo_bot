from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.webhook import SendMessage
from logfmt_logger import getLogger

from cost_my_chemo_bot.bots.telegram import dispatcher, filters
from cost_my_chemo_bot.bots.telegram.state import Form, parse_state
from cost_my_chemo_bot.config import SETTINGS

logger = getLogger(__name__, level=SETTINGS.LOG_LEVEL)


@dispatcher.dp.callback_query_handler(filters.back_valid, state="*")
@dispatcher.dp.message_handler(filters.back_valid, state="*")
async def back_handler(
    callback_or_message: types.CallbackQuery | types.Message, state: FSMContext
) -> types.Message | SendMessage:
    if isinstance(callback_or_message, types.CallbackQuery):
        message = callback_or_message.message
    else:
        message = callback_or_message
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
    match current_state:
        case Form.initial.state:
            await state.update_data(initial=None)
            return await dispatcher.send_welcome_message(message=message)
        case Form.height.state:
            await state.update_data(height=None)
            return await dispatcher.send_height_message(message=message)
        case Form.weight.state:
            await state.update_data(weight=None)
            return await dispatcher.send_weight_message(message=message)
        case Form.category.state:
            await state.update_data(category=None)
            return await dispatcher.send_category_message(message=message)
        case Form.nosology.state:
            await state.update_data(nosology=None)
            if state_data.is_accompanying_therapy:
                await state.set_state(Form.category)
                return await dispatcher.send_category_message(message=message)

            return await dispatcher.send_nosology_message(
                message=message,
                state=state,
            )
        case Form.course.state:
            await state.update_data(course=None)
            return await dispatcher.send_course_message(
                message=message,
                category_id=state_data.category_id,
                nosology_id=state_data.nosology_id,
            )
        case Form.data_confirmation.state:
            await state.update_data(data_confirmation=None)
            return await dispatcher.send_data_confirmation_message(
                message=message,
                state=state,
            )
        case Form.contacts_input.state:
            await state.update_data(contacts_input=None)
            return await dispatcher.send_contacts_input_message(
                message=message,
                state=state,
            )
        case Form.first_name.state:
            await state.update_data(first_name=None)
            return await dispatcher.send_first_name_message(message=message)
        case Form.last_name.state:
            await state.update_data(last_name=None)
            return await dispatcher.send_last_name_message(message=message)
        case Form.email.state:
            await state.update_data(email=None)
            return await dispatcher.send_email_message(message=message)
        case Form.phone_number.state:
            await state.update_data(phone_number=None)
            return await dispatcher.send_phone_number_message(message=message)
