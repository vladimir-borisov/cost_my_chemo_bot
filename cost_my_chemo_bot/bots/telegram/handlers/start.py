from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.webhook import SendMessage
from logfmt_logger import getLogger

from cost_my_chemo_bot.bots.telegram import dispatcher, filters
from cost_my_chemo_bot.bots.telegram.state import Form
from cost_my_chemo_bot.action_logger.main import action_logger


logger = getLogger(__name__)


async def start_handler(
        callback_or_message: types.CallbackQuery | types.Message,
        state: FSMContext) -> types.Message | SendMessage:

    dp = Dispatcher.get_current()

    if isinstance(callback_or_message, types.CallbackQuery):
        message = callback_or_message.message
    else:
        message = callback_or_message

    if hasattr(dp.storage, "release_lock"):
        logger.info("Releasing lock")
        await dp.storage.release_lock(chat=message.chat.id, user=message.from_user.id)

    return await dispatcher.send_start_message(message=message)


async def start_yes_click(
        callback_or_message: types.CallbackQuery | types.Message,
        state: FSMContext) -> types.Message | SendMessage:

    if isinstance(callback_or_message, types.CallbackQuery):
        message = callback_or_message.message
    else:
        message = callback_or_message

    await action_logger.send_message(message="Пользователь нажал 'Да'",
                                     user_id=message.chat.id,
                                     username=f"{message.chat.first_name} {message.chat.last_name}")

    await state.set_state(Form.height)

    return await dispatcher.send_height_message(message=message)


def init_start_handlers(dp: Dispatcher):

    dp.register_message_handler(
        start_handler,
        state=Form.start,
    )

    dp.register_callback_query_handler(
        start_yes_click,
        filters.start_step_confirmed,
        state=Form.start
    )
