import httpx
from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.webhook import SendMessage
from logfmt_logger import getLogger

from cost_my_chemo_bot.bots.telegram import dispatcher, filters, messages
from cost_my_chemo_bot.bots.telegram.send import send_message
from cost_my_chemo_bot.bots.telegram.state import Form, parse_state
from cost_my_chemo_bot.config import SETTINGS

logger = getLogger(__name__)


async def save_lead(message: types.Message, state: FSMContext):
    state_data = await parse_state(state=state)

    params = {
        "FIELDS[TITLE]": "Новый лид",
        "FIELDS[NAME]": state_data.first_name,
        "FIELDS[LAST_NAME": state_data.last_name,
        "FIELDS[EMAIL][0][VALUE]": state_data.email,
        "FIELDS[EMAIL][0][VALUE_TYPE]": "WORK",
        "FIELDS[PHONE][0][VALUE]": state_data.phone_number,
        "FIELDS[PHONE][0][VALUE_TYPE]": "WORK",
    }
    logger.info("save lead: %s", params)
    async with httpx.AsyncClient(base_url=SETTINGS.BITRIX_URL) as client:
        resp = await client.post("", params=params)

    if resp.status_code != 200:
        logger.error("save lead: %s", resp.text)
    else:
        logger.info("save lead: %s", resp.text)


async def process_first_name(
    message: types.Message, state: FSMContext
) -> types.Message | SendMessage:
    await state.update_data(first_name=message.text)
    await state.set_state(Form.last_name)
    return await dispatcher.send_last_name_message(message=message)


async def process_last_name(
    message: types.Message, state: FSMContext
) -> types.Message | SendMessage:
    await state.update_data(last_name=message.text)
    await state.set_state(Form.email)
    return await dispatcher.send_email_message(message=message)


async def process_email(
    message: types.Message, state: FSMContext
) -> types.Message | SendMessage:
    await state.update_data(email=message.text)
    await state.set_state(Form.phone_number)
    return await dispatcher.send_phone_number_message(message=message)


async def process_email_invalid(
    message: types.Message, state: FSMContext
) -> types.Message | SendMessage:
    return await dispatcher.send_email_invalid_message(message=message)


async def process_phone_number(
    message: types.Message, state: FSMContext
) -> types.Message | SendMessage:
    await state.update_data(phone_number=message.text)
    await save_lead(message=message, state=state)
    return await send_message(
        dispatcher.bot,
        chat_id=message.chat.id,
        text=messages.THANKS,
        reply_markup=types.ReplyKeyboardRemove(),
    )


def init_handlers(dp: Dispatcher):
    dp.register_message_handler(process_first_name, state=Form.first_name)
    dp.register_message_handler(process_last_name, state=Form.last_name)
    dp.register_message_handler(process_email, filters.email_valid, state=Form.email)
    dp.register_message_handler(
        process_email_invalid, filters.email_invalid, state=Form.email
    )
    dp.register_message_handler(process_phone_number, state=Form.phone_number)
