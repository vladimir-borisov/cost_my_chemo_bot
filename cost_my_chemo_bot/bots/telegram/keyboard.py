import enum
import typing

from aiogram import types
from logfmt_logger import getLogger

logger = getLogger(__name__)


class Buttons(enum.Enum):
    WELCOME_START = types.InlineKeyboardButton(text="Начать", callback_data="welcome_start")
    YES = types.InlineKeyboardButton(text="✅ Да", callback_data="yes")
    NEED_CORRECTION = types.InlineKeyboardButton(
        text="✏ Нет, нужно исправить", callback_data="need_correction"
    )
    BACK = types.InlineKeyboardButton("↩ Назад", callback_data="back")
    MENU = types.InlineKeyboardButton("#️⃣  В начало", callback_data="menu")
    CONTACTS_INPUT = types.InlineKeyboardButton(
        "☎ Ввести контакты", callback_data="contacts_input"
    )
    SKIP = types.InlineKeyboardButton("↪ Пропустить", callback_data="skip")
    CUSTOM_COURSE = types.InlineKeyboardButton(
        "❓Не нашли свой курс?", callback_data="custom_course"
    )


def get_keyboard_markup(
    buttons: typing.Iterable[str | types.InlineKeyboardButton | types.KeyboardButton] = tuple(),
    inline: bool = True,
) -> types.ReplyKeyboardMarkup | types.InlineKeyboardMarkup:

    if inline:

        keyboard_markup = types.InlineKeyboardMarkup()

        for button in buttons:
            if isinstance(button, str):
                keyboard_markup.add(
                    types.InlineKeyboardButton(
                        text=button,
                        callback_data=button,
                    )
                )
            elif isinstance(button, types.InlineKeyboardButton):
                keyboard_markup.add(button)
            else:
                logger.warning("can't add button of type: %s", type(button))
                continue

        keyboard_markup.row(
            Buttons.BACK.value,
            Buttons.MENU.value,
        )
        return keyboard_markup

    return types.ReplyKeyboardMarkup(
        [
            *[[button] for button in buttons],
            [Buttons.BACK.value.text, Buttons.MENU.value.text],
        ],
        one_time_keyboard=True,
        resize_keyboard=False,
        selective=True,
    )
