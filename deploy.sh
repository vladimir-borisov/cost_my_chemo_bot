#!env bash
gcloud functions deploy cost-my-chemo-bot \
    --gen2 \
    --runtime=python310 \
    --region=europe-west1 \
    --source=. \
    --entry-point=process_webhook \
    --trigger-http \
    --allow-unauthenticated \
    --env-vars-file=cloud_env.yaml \
    --min-instances=0 \
    --max-instances=1 \
    --memory=128Mi
