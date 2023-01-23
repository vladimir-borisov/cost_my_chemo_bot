from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import CommandStart
from aiogram.dispatcher.webhook import SendMessage
from logfmt_logger import getLogger

from cost_my_chemo_bot.bots.telegram import dispatcher, filters
from cost_my_chemo_bot.bots.telegram.state import Form

logger = getLogger(__name__)


async def welcome_handler(
    callback_or_message: types.CallbackQuery | types.Message, state: FSMContext
) -> types.Message | SendMessage:
    logger.info(__name__)
    if isinstance(callback_or_message, types.CallbackQuery):
        message = callback_or_message.message
    else:
        message = callback_or_message

    if hasattr(dispatcher.dp.storage, "release_lock"):
        logger.info(
            "Releasing lock",
        )
        await dispatcher.dp.storage.release_lock(
            chat=message.chat.id, user=message.from_user.id
        )

    current_state = await state.get_state()
    if current_state is not None:
        logger.info("Cancelling state %r", current_state)
        await state.finish()

    await state.update_data(initial=True)
    await state.set_state(Form.initial)
    return await dispatcher.send_welcome_message(message=message, initial=True)


async def process_initial_step(
    callback_or_message: types.CallbackQuery | types.Message, state: FSMContext
) -> types.Message | SendMessage:
    if isinstance(callback_or_message, types.CallbackQuery):
        message = callback_or_message.message
    else:
        message = callback_or_message

    await state.set_state(Form.height)
    return await dispatcher.send_height_message(message=message)


def init_welcome_handlers(dp: Dispatcher):
    # We need to register welcome handler with each filter separately, because
    # it won't process commands otherwise.
    dp.register_message_handler(
        welcome_handler,
        CommandStart(),
        state="*",
    )
    dp.register_message_handler(
        welcome_handler,
        filters.welcome_message,
        state="*",
    )
    dp.register_message_handler(
        welcome_handler,
        filters.welcome_message_text,
        state="*",
    )
    dp.register_callback_query_handler(
        welcome_handler, filters.welcome_callback, state="*"
    )
    dp.register_callback_query_handler(
        process_initial_step, filters.initial_step_confirmed, state=Form.initial
    )
