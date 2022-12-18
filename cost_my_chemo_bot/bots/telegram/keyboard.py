import logging
import typing

from aiogram import types


def get_keyboard_markup(
    buttons: typing.Iterable = tuple(),
    inline: bool = True,
) -> types.ReplyKeyboardMarkup:
    if inline:
        keyboard_markup = types.InlineKeyboardMarkup(row_width=3)
        for button in buttons:
            keyboard_markup.add(
                types.InlineKeyboardButton(button, callback_data=button)
            )

        keyboard_markup.row(
            types.InlineKeyboardButton("Back", callback_data="back"),
            types.InlineKeyboardButton("Menu", callback_data="Menu"),
        )
        return keyboard_markup
        # return types.InlineKeyboardMarkup(
        #     inline_keyboard=[
        #         [
        #             types.InlineKeyboardButton(text=button, callback_data=button)
        #             for button in buttons
        #         ],
        #         ["Back", "Menu"],
        #     ]
        # )

    return types.ReplyKeyboardMarkup(
        [*[[button] for button in buttons], ["Back", "Menu"]],
        resize_keyboard=False,
        selective=True,
    )
