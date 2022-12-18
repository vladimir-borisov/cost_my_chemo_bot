import base64
import typing

from aiogram import types


def get_keyboard_markup(
    buttons: typing.Iterable[str] = tuple(),
    inline: bool = True,
    index_callback: bool = False,
) -> types.ReplyKeyboardMarkup:
    if inline:
        keyboard_markup = types.InlineKeyboardMarkup()
        for i, button in enumerate(buttons):
            keyboard_markup.add(
                types.InlineKeyboardButton(
                    text=button,
                    callback_data=i if index_callback else button,
                )
            )

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
