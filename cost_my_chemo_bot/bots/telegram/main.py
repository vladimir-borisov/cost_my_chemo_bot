from aiogram import Dispatcher, executor
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from logfmt_logger import getLogger

# to register all handlers in dispatcher
import cost_my_chemo_bot.bots.telegram.handlers  # noqa
from cost_my_chemo_bot.bots.telegram.dispatcher import bot, dp
from cost_my_chemo_bot.bots.telegram.handlers import init_handlers
from cost_my_chemo_bot.config import SETTINGS, WEBHOOK_SETTINGS, BotMode
from cost_my_chemo_bot.db import DB

logger = getLogger(__name__)


async def on_startup(dp: Dispatcher):
    init_handlers(dp)
    if SETTINGS.SET_COMMANDS:
        await bot.set_my_commands(commands=[])
    database = DB()
    await database.load_db()
    if SETTINGS.BOT_MODE is BotMode.WEBHOOK and WEBHOOK_SETTINGS.SET_WEBHOOK:
        logger.info(
            "set webhook to url: %s: %s",
            WEBHOOK_SETTINGS.webhook_url,
            await bot.set_webhook(WEBHOOK_SETTINGS.webhook_url),
        )


async def on_shutdown(dp):
    logger.warning("Shutting down...")

    if SETTINGS.BOT_MODE is BotMode.WEBHOOK and WEBHOOK_SETTINGS.SET_WEBHOOK:
        await bot.delete_webhook()

    await dp.storage.close()
    await dp.storage.wait_closed()

    logger.warning("Bye!")


if __name__ == "__main__":
    # Configure logging
    getLogger("aiogram", level=SETTINGS.LOG_LEVEL)
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
