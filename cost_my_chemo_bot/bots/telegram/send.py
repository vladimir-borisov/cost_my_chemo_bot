from aiogram import Bot, types
from aiogram.dispatcher.webhook import SendMessage

from cost_my_chemo_bot.config import SETTINGS, BotMode


async def send_message(
    bot: Bot,
    *,
    chat_id: int | str = None,
    text: str | None = None,
    parse_mode: str | None = None,
    disable_web_page_preview: bool | None = None,
    disable_notification: bool | None = None,
    protect_content: bool | None = None,
    reply_to_message_id: int | None = None,
    reply_markup: types.InlineKeyboardMarkup
    | types.ReplyKeyboardMarkup
    | dict
    | str
    | None = None,
) -> types.Message | SendMessage:
    if SETTINGS.BOT_MODE is BotMode.WEBHOOK:
        return SendMessage(
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode,
            disable_web_page_preview=disable_web_page_preview,
            disable_notification=disable_notification,
            protect_content=protect_content,
            reply_to_message_id=reply_to_message_id,
            reply_markup=reply_markup,
        )

    return await bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=parse_mode,
        disable_web_page_preview=disable_web_page_preview,
        disable_notification=disable_notification,
        protect_content=protect_content,
        reply_to_message_id=reply_to_message_id,
        reply_markup=reply_markup,
    )
