from aiogram import Dispatcher, executor, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from logfmt_logger import getLogger

from cost_my_chemo_bot.bots.telegram.bot import close_bot, init_bot, make_bot
from cost_my_chemo_bot.bots.telegram.dispatcher import make_dispatcher
from cost_my_chemo_bot.bots.telegram.handlers import init_handlers
from cost_my_chemo_bot.bots.telegram.storage import make_storage
from cost_my_chemo_bot.config import SETTINGS, WEBHOOK_SETTINGS, BotMode
from cost_my_chemo_bot.db import DB

logger = getLogger(__name__)


async def on_startup(dp: Dispatcher):
    await init_bot(bot=dp.bot, dp=dp)


async def on_shutdown(dp):
    await close_bot(bot=dp.bot, dp=dp)


if __name__ == "__main__":
    # Configure logging
    getLogger("aiogram", level=SETTINGS.LOG_LEVEL)
    bot = make_bot()
    storage = make_storage()
    dp = make_dispatcher(bot, storage=storage)
    dp.middleware.setup(LoggingMiddleware())
    if SETTINGS.BOT_MODE is BotMode.POLLING:
        executor.start_polling(
            dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown
        )
    elif SETTINGS.BOT_MODE is BotMode.WEBHOOK:
        executor.start_webhook(
            dp,
            webhook_path=WEBHOOK_SETTINGS.WEBHOOK_PATH,
            skip_updates=True,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            host=WEBHOOK_SETTINGS.WEBAPP_HOST,
            port=WEBHOOK_SETTINGS.WEBAPP_PORT,
        )
