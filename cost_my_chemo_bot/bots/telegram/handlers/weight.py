from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.webhook import SendMessage
from logfmt_logger import getLogger

from cost_my_chemo_bot.bots.telegram import dispatcher, filters, messages
from cost_my_chemo_bot.bots.telegram.keyboard import get_keyboard_markup
from cost_my_chemo_bot.bots.telegram.send import send_message
from cost_my_chemo_bot.bots.telegram.state import Form

logger = getLogger(__name__)


async def process_weight(
    message: types.Message, state: FSMContext
) -> types.Message | SendMessage:
    await state.update_data(weight=int(message.text))
    await state.set_state(Form.category)
    return await dispatcher.send_category_message(message=message)


async def process_weight_invalid(message: types.Message):
    bot = Bot.get_current()

    return await send_message(
        bot,
        chat_id=message.chat.id,
        text=messages.WEIGHT_WRONG,
        reply_markup=get_keyboard_markup(),
    )


def init_weight_handlers(dp: Dispatcher):
    dp.register_message_handler(process_weight, filters.weight_valid, state=Form.weight)

    dp.register_message_handler(
        process_weight_invalid, filters.weight_invalid, state=Form.weight
    )
