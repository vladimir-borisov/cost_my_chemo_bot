import logging

from aiogram import types
from aiogram.dispatcher import FSMContext

from cost_my_chemo_bot.bots.telegram import dispatcher, messages
from cost_my_chemo_bot.bots.telegram.state import Form

logger = logging.getLogger(__name__)


@dispatcher.dp.message_handler(state=Form.lead, content_types=types.ContentType.CONTACT)
async def process_lead(message: types.Message, state: FSMContext):
    logger.info("%s", message.contact)
    await state.update_data(lead=message.contact.as_json())
    await state.set_state(None)
    await message.reply(messages.THANKS, reply_markup=types.ReplyKeyboardRemove())
