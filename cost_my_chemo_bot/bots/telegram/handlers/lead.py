import httpx
from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.webhook import SendMessage
from logfmt_logger import getLogger

from cost_my_chemo_bot.bots.telegram import dispatcher, filters
from cost_my_chemo_bot.bots.telegram.state import Form, parse_state
from cost_my_chemo_bot.config import SETTINGS
from cost_my_chemo_bot.action_logger.main import action_logger


logger = getLogger(__name__)


async def save_lead(message: types.Message, state: FSMContext):
    state_data = await parse_state(state=state)

    params = {
        "FIELDS[TITLE]": 'Новый лид из тг-бота "ЛуЛа"',
        "FIELDS[NAME]": state_data.first_name,
        "FIELDS[LAST_NAME]": state_data.last_name,
        "FIELDS[EMAIL][0][VALUE]": state_data.email,
        "FIELDS[EMAIL][0][VALUE_TYPE]": "WORK",
        "FIELDS[PHONE][0][VALUE]": state_data.phone_number,
        "FIELDS[PHONE][0][VALUE_TYPE]": "WORK",
        "FIELDS[COMMENTS]": f"""
                                 Курс: {state_data.course_name} | Вес: {state_data.weight} | Рост: {state_data.height} |
                                 Стоимость курса: {state_data.course_price} 
                             """,
    }
    logger.info("save lead: %s", params)
    async with httpx.AsyncClient(base_url=SETTINGS.BITRIX_URL) as client:
        resp = await client.post(
            f"{SETTINGS.BITRIX_TOKEN.get_secret_value()}/crm.lead.add.json",
            params=params,
        )

    if resp.status_code != 200:
        logger.error("save lead: %s", resp.text)
    else:
        logger.info("save lead: %s", resp.text)


async def process_contacts_input(
    callback: types.CallbackQuery, state: FSMContext
) -> types.Message | SendMessage:
    message = callback.message

    await action_logger.send_message(message="Пользователь нажал кнопку 'Ввести контакты'",
                                     user_id=message.chat.id,
                                     username=f"{message.chat.first_name} {message.chat.last_name}")


    await state.update_data(contacts_input=callback.data)
    await state.set_state(Form.first_name)
    return await dispatcher.send_first_name_message(message=message)


async def process_first_name(
    message: types.Message, state: FSMContext
) -> types.Message | SendMessage:

    if message.text is not None:
        await action_logger.send_message(message=f"Пользователь ввел имя: {message.text}",
                                         user_id=message.chat.id,
                                         username=f"{message.chat.first_name} {message.chat.last_name}")

    await state.update_data(first_name=message.text)
    await state.set_state(Form.last_name)
    return await dispatcher.send_last_name_message(message=message)


async def process_last_name(
    message: types.Message, state: FSMContext
) -> types.Message | SendMessage:

    if message.text is not None:
        await action_logger.send_message(message=f"Пользователь ввел фамилию: {message.text}",
                                         user_id=message.chat.id,
                                         username=f"{message.chat.first_name} {message.chat.last_name}")

    await state.update_data(last_name=message.text)
    await state.set_state(Form.email)
    return await dispatcher.send_email_message(message=message)


async def process_email(
    message: types.Message, state: FSMContext
) -> types.Message | SendMessage:

    if message.text is not None:
        await action_logger.send_message(message=f"Пользователь ввел почту: {message.text}",
                                         user_id=message.chat.id,
                                         username=f"{message.chat.first_name} {message.chat.last_name}")

    await state.update_data(email=message.text)
    await state.set_state(Form.phone_number)
    return await dispatcher.send_phone_number_message(message=message)


async def process_email_invalid(
    message: types.Message, state: FSMContext
) -> types.Message | SendMessage:

    await action_logger.send_message(message=f"Пользователь неправильно ввел почту: {message.text}",
                                     user_id=message.chat.id,
                                     username=f"{message.chat.first_name} {message.chat.last_name}")

    return await dispatcher.send_email_invalid_message(message=message)


async def process_phone_number(
    message: types.Message, state: FSMContext
) -> types.Message | SendMessage:

    if message.text is not None:
        await action_logger.send_message(message=f"Пользователь ввел телефон: {message.text}",
                                         user_id=message.chat.id,
                                         username=f"{message.chat.first_name} {message.chat.last_name}")

    await state.update_data(phone_number=message.text)
    await state.set_state(Form.lead_confirmation)
    return await dispatcher.send_lead_confirmation_message(message=message, state=state)


async def process_phone_number_invalid(
    message: types.Message, state: FSMContext
) -> types.Message | SendMessage:

    await action_logger.send_message(message=f"Пользователь неправильно ввел телефон: {message.text}",
                                     user_id=message.chat.id,
                                     username=f"{message.chat.first_name} {message.chat.last_name}")

    return await dispatcher.send_phone_number_invalid_message(message=message)


async def process_lead_confirmation(
    callback: types.CallbackQuery, state: FSMContext
) -> types.Message | SendMessage:
    message = callback.message

    await action_logger.send_message(message=f"Пользователь подтвердил отправку контактных данных",
                                     user_id=message.chat.id,
                                     username=f"{message.chat.first_name} {message.chat.last_name}")

    await save_lead(message=message, state=state)
    await state.finish()
    return await dispatcher.send_final_message(message=message)


async def process_lead_reenter(callback: types.CallbackQuery, state: FSMContext):
    message = callback.message

    await action_logger.send_message(message=f"Пользователь решил исправить контактные данные",
                                     user_id=message.chat.id,
                                     username=f"{message.chat.first_name} {message.chat.last_name}")

    await state.set_state(Form.first_name)
    return await dispatcher.send_first_name_message(message=message)


async def process_skip(
    callback: types.CallbackQuery, state: FSMContext
) -> types.Message | SendMessage:

    message = callback.message
    current_state = await state.get_state()

    if current_state == Form.first_name.state:

        await action_logger.send_message(message=f"Пользователь пропустил ввод имени",
                                         user_id=message.chat.id,
                                         username=f"{message.chat.first_name} {message.chat.last_name}")

        message.text = None
        return await process_first_name(message=message, state=state)

    if current_state == Form.last_name.state:

        await action_logger.send_message(message=f"Пользователь пропустил ввод фамилии",
                                         user_id=message.chat.id,
                                         username=f"{message.chat.first_name} {message.chat.last_name}")

        message.text = None
        return await process_last_name(message=message, state=state)
    if current_state == Form.email.state:

        await action_logger.send_message(message=f"Пользователь пропустил ввод почты",
                                         user_id=message.chat.id,
                                         username=f"{message.chat.first_name} {message.chat.last_name}")

        message.text = None
        return await process_email(message=message, state=state)

    if current_state == Form.phone_number.state:

        await action_logger.send_message(message=f"Пользователь пропустил ввод телефона",
                                         user_id=message.chat.id,
                                         username=f"{message.chat.first_name} {message.chat.last_name}")

        message.text = None
        return await process_phone_number(message=message, state=state)


def init_lead_handlers(dp: Dispatcher):

    dp.register_callback_query_handler(process_contacts_input, filters.contacts_input, state=Form.contacts_input)

    dp.register_message_handler(process_first_name, filters.first_name_valid, state=Form.first_name)
    dp.register_message_handler(process_last_name, filters.last_name_valid, state=Form.last_name)

    dp.register_message_handler(process_email, filters.email_valid, state=Form.email)
    dp.register_message_handler(process_email_invalid, filters.email_invalid, state=Form.email)

    dp.register_message_handler(process_phone_number, filters.phone_number_valid, state=Form.phone_number)
    dp.register_message_handler(process_phone_number_invalid, filters.phone_number_invalid, state=Form.phone_number)

    dp.register_callback_query_handler(process_lead_confirmation, filters.lead_confirmed, state=Form.lead_confirmation)
    dp.register_callback_query_handler(process_lead_reenter, filters.lead_reenter, state=Form.lead_confirmation)

    dp.register_callback_query_handler(process_skip, filters.skip, state=Form.first_name)
    dp.register_callback_query_handler(process_skip, filters.skip, state=Form.last_name)
    dp.register_callback_query_handler(process_skip, filters.skip, state=Form.email)
    dp.register_callback_query_handler(process_skip, filters.skip, state=Form.phone_number)
