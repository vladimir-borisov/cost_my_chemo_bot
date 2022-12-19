import logging

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.webhook import SendMessage

from cost_my_chemo_bot.bots.telegram import dispatcher, filters
from cost_my_chemo_bot.bots.telegram.state import Form

logger = logging.getLogger(__name__)


@dispatcher.dp.callback_query_handler(filters.welcome_callback, state="*")
@dispatcher.dp.message_handler(filters.welcome_message, state="*")
async def welcome_handler(
    callback_or_message: types.CallbackQuery | types.Message, state: FSMContext
) -> types.Message | SendMessage:
    if isinstance(callback_or_message, types.CallbackQuery):
        message = callback_or_message.message
    else:
        message = callback_or_message

    logger.info(
        "all_states: %s, all_states_names: %s", Form.all_states, Form.all_states_names
    )
    current_state = await state.get_state()
    if current_state is not None:
        logger.info("Cancelling state %r", current_state)
        await state.finish()

    await state.set_state(Form.height)
    return await dispatcher.send_height_message(message=message, initial=True)
