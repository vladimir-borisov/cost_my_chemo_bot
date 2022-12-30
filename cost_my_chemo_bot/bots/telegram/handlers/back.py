import logging

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.webhook import SendMessage

from cost_my_chemo_bot.bots.telegram import dispatcher, filters
from cost_my_chemo_bot.bots.telegram.state import Form, parse_state

logger = logging.getLogger(__name__)


@dispatcher.dp.callback_query_handler(filters.back_valid, state="*")
@dispatcher.dp.message_handler(filters.back_valid, state="*")
async def back_handler(
    callback_or_message: types.CallbackQuery | types.Message, state: FSMContext
) -> types.Message | SendMessage:
    logger.info("state=%s", state)
    local_dispatcher = callback_or_message.bot
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
        case Form.height.state:
            return await dispatcher.send_height_message(message=message)
        case Form.weight.state:
            return await dispatcher.send_weight_message(message=message)
        case Form.category.state:
            return await dispatcher.send_category_message(message=message)
        case Form.nosology.state:
            return await dispatcher.send_nosology_message(
                message=message,
                state=state,
            )
        case Form.course.state:
            return await dispatcher.send_course_message(
                message=message,
                category_id=state_data.category_id,
                nosology_id=state_data.nosology_id,
            )
        case Form.lead.state:
            return await dispatcher.send_lead_message(message=message)
