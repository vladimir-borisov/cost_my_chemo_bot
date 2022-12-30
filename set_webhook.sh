#!env bash
curl -F "url=https://cost-my-chemo-bot-ituksvxabq-ew.a.run.app"\
    "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook"
