from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command, Text
from aiogram.dispatcher.webhook import SendMessage
from logfmt_logger import getLogger

from cost_my_chemo_bot.bots.telegram import messages
from cost_my_chemo_bot.bots.telegram.send import send_message
from cost_my_chemo_bot.action_logger.main import action_logger

logger = getLogger(__name__)


async def cancel_handler(
    callback_or_message: types.CallbackQuery | types.Message, state: FSMContext
) -> types.Message | SendMessage:

    bot = Bot.get_current()

    if isinstance(callback_or_message, types.CallbackQuery):
        message = callback_or_message.message
    else:
        message = callback_or_message

    await action_logger.send_message(message=f"Пользователь ввел команду /stop",
                                     user_id=message.chat.id,
                                     username=f"{message.chat.first_name} {message.chat.last_name}")

    current_state = await state.get_state()
    logger.info("Cancelling state %r", current_state)
    await state.finish()
    return await send_message(
        bot,
        chat_id=message.chat.id,
        text=messages.GOODBYE,
        reply_markup=types.ReplyKeyboardRemove(),
    )


def init_cancel_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(
        cancel_handler, Text(equals=["stop"], ignore_case=True), state="*"
    )
    dp.register_message_handler(cancel_handler, Command(commands=["stop"]), state="*")
