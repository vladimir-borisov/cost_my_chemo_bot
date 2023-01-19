import typing

from aiogram import types
from logfmt_logger import getLogger

logger = getLogger(__name__)


def get_keyboard_markup(
    buttons: typing.Iterable[
        str | types.InlineKeyboardButton | types.KeyboardButton
    ] = tuple(),
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
            types.InlineKeyboardButton("Back", callback_data="back"),
            types.InlineKeyboardButton("Menu", callback_data="menu"),
        )
        return keyboard_markup

    return types.ReplyKeyboardMarkup(
        [*[[button] for button in buttons], ["Back", "Menu"]],
        one_time_keyboard=True,
        resize_keyboard=False,
        selective=True,
    )
