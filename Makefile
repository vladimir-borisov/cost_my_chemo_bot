.DEFAULT_GOAL := check_webhook

deploy:
	bash scripts/deploy.sh

check_webhook:
	bash scripts/check_webhook.sh

set_webhook:
	bash scripts/set_webhook.sh

set_webhook_local:
	bash scripts/set_webhook_local.sh