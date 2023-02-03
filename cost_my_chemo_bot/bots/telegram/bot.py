from aiogram import Bot

from cost_my_chemo_bot.config import SETTINGS


def make_bot() -> Bot:
    return Bot(token=SETTINGS.TELEGRAM_BOT_TOKEN)
