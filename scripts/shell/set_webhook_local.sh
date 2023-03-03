#!env /bin/bash
set -euxo pipefail
curl -F "url=https://af52-188-169-169-120.eu.ngrok.io"\
    "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook"
