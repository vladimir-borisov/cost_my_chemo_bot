from aiogram import Bot, Dispatcher, types
from logfmt_logger import getLogger

from cost_my_chemo_bot.bots.telegram.handlers import init_handlers
from cost_my_chemo_bot.config import SETTINGS, WEBHOOK_SETTINGS, BotMode
from cost_my_chemo_bot.db import DB

logger = getLogger(__name__)


def make_bot() -> Bot:
    return Bot(token=SETTINGS.TELEGRAM_BOT_TOKEN)


async def init_bot(bot: Bot, dp: Dispatcher):
    getLogger("aiogram", level=SETTINGS.LOG_LEVEL)
    getLogger("uvicorn", level=SETTINGS.LOG_LEVEL)
    getLogger("asyncio", level=SETTINGS.LOG_LEVEL)

    if SETTINGS.SET_COMMANDS:
        await bot.set_my_commands(
            commands=[
                types.BotCommand(command="/start", description="Начать сначала"),
                types.BotCommand(command="/stop", description="Стоп"),
            ]
        )

    database = DB()
    await database.load_db()

    Dispatcher.set_current(dp)
    Bot.set_current(bot)
    if SETTINGS.BOT_MODE is BotMode.WEBHOOK and WEBHOOK_SETTINGS.SET_WEBHOOK:
        logger.info(
            "set webhook to url: %s: %s",
            WEBHOOK_SETTINGS.webhook_url,
            await bot.set_webhook(WEBHOOK_SETTINGS.webhook_url),
        )
    init_handlers(dp)


async def close_bot(bot: Bot, dp: Dispatcher):
    Dispatcher.set_current(dp)
    Bot.set_current(bot)
    await dp.storage.close()
    await dp.storage.wait_closed()
    await DB.close()
    session = await dp.bot.get_session()
    await session.close()
