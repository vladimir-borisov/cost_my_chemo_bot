from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import CommandStart
from aiogram.dispatcher.webhook import SendMessage
from logfmt_logger import getLogger

from cost_my_chemo_bot.bots.telegram import dispatcher, filters
from cost_my_chemo_bot.bots.telegram.state import Form
from cost_my_chemo_bot.action_logger.main import action_logger

logger = getLogger(__name__)


async def welcome_handler(
    callback_or_message: types.CallbackQuery | types.Message,
    state: FSMContext
) -> types.Message | SendMessage:

    dp = Dispatcher.get_current()

    if isinstance(callback_or_message, types.CallbackQuery):
        message = callback_or_message.message

        if callback_or_message.data == 'menu':
            await action_logger.send_message(message="Пользователь нажал 'В начало'",
                                             user_id=message.chat.id,
                                             username=f"{message.chat.first_name} {message.chat.last_name}")

    else:
        message = callback_or_message

    if hasattr(dp.storage, "release_lock"):
        logger.info(
            "Releasing lock",
        )
        await dp.storage.release_lock(chat=message.chat.id, user=message.from_user.id)

    current_state = await state.get_state()
    if current_state is not None:
        logger.info("Cancelling state %r", current_state)
        await state.finish()

    return await dispatcher.send_welcome_message(message=message)


async def process_initial_step(
    callback_or_message: types.CallbackQuery | types.Message, state: FSMContext
) -> types.Message | SendMessage:

    if isinstance(callback_or_message, types.CallbackQuery):
        message = callback_or_message.message
    else:
        message = callback_or_message

    await action_logger.send_message(message="Пользователь нажал 'Начать'",
                                     user_id=message.chat.id,
                                     username=f"{message.chat.first_name} {message.chat.last_name}")

    # activate next state - Start
    await state.set_state(Form.start)

    # send message from the next state
    return await dispatcher.send_start_message(message=message)


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
        welcome_handler,
        filters.welcome_callback,
        state="*"
    )
    dp.register_callback_query_handler(
        process_initial_step,
        filters.welcome_step_confirmed,
        state="*"
    )
