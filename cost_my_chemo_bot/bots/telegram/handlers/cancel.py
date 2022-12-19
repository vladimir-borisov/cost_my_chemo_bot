import logging

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command, Text
from aiogram.dispatcher.webhook import SendMessage

from cost_my_chemo_bot.bots.telegram import dispatcher, messages
from cost_my_chemo_bot.bots.telegram.send import send_message

logger = logging.getLogger(__name__)


@dispatcher.dp.callback_query_handler(
    Text(equals=["stop"], ignore_case=True), state="*"
)
@dispatcher.dp.message_handler(Command(commands=["stop"]), state="*")
async def cancel_handler(
    callback_or_message: types.CallbackQuery | types.Message, state: FSMContext
) -> types.Message | SendMessage:
    if isinstance(callback_or_message, types.CallbackQuery):
        message = callback_or_message.message
    else:
        message = callback_or_message

    current_state = await state.get_state()
    logger.info("Cancelling state %r", current_state)
    await state.finish()
    return await send_message(
        dispatcher.bot,
        chat_id=message.chat.id,
        text=messages.GOODBYE,
        reply_markup=types.ReplyKeyboardRemove(),
    )
