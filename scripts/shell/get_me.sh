#!env /bin/bash
set -euxo pipefail
curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe"
