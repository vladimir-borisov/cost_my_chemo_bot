import logging

from aiogram import executor
from aiogram.contrib.middlewares.logging import LoggingMiddleware

# to register all handlers in dispatcher
import cost_my_chemo_bot.bots.telegram.handlers  # noqa
from cost_my_chemo_bot.bots.telegram.dispatcher import bot, dp
from cost_my_chemo_bot.config import SETTINGS, WEBHOOK_SETTINGS, BotMode
from cost_my_chemo_bot.db import DB

logger = logging.getLogger(__name__)


async def on_startup(dp):
    database = DB()
    await database.load_db()
    if (
        SETTINGS.BOT_MODE
        is BotMode.WEBHOOK
        # and not WEBHOOK_SETTINGS.WEBHOOK_HOST.startswith("http://")
    ):
        logger.info(
            "set webhook: %s", await bot.set_webhook(WEBHOOK_SETTINGS.webhook_url)
        )


async def on_shutdown(dp):
    logger.warning("Shutting down...")

    if SETTINGS.BOT_MODE is BotMode.WEBHOOK:
        await bot.delete_webhook()

    await dp.storage.close()
    await dp.storage.wait_closed()

    logger.warning("Bye!")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=SETTINGS.LOG_LEVEL)
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
