import logging
import typing

from aiogram import types


def get_keyboard_markup(
    buttons: typing.Iterable = tuple(),
) -> types.ReplyKeyboardMarkup:
    return types.ReplyKeyboardMarkup(
        [*[[button] for button in buttons], ["Back", "Menu"]],
        resize_keyboard=False,
        selective=True,
    )
