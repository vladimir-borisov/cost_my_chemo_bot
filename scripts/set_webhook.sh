#!env bash
curl -F "url=$(gcloud functions describe cost-my-chemo-bot --region=europe-west1 --format="value(serviceConfig.uri)")"\
    "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook"
