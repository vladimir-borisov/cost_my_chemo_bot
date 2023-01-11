#!env /bin/bash
set -euxo pipefail
curl -F "url=$(gcloud functions describe cost-my-chemo-bot --region=europe-west1 --format="value(serviceConfig.uri)")"\
    "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook"
# curl -F "url=https://af52-188-169-169-120.eu.ngrok.io"\
#     "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook"
