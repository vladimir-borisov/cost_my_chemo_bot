.DEFAULT_GOAL := help

help:
	@awk 'BEGIN {FS = ":.*##"; printf "Usage:\n  make \033[36m<target>\033[0m\n\nTargets:\n"} /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-10s\033[0m -%s\n", $$1, $$2 }' $(MAKEFILE_LIST)

format: ## Black + isort + autoflake
	autoflake -r --remove-all-unused-imports -i ./
	black .
	isort .

deploy:  ## Deploy google cloud function
	bash scripts/deploy.sh

check_webhook:  ## Print this bot webhook
	bash scripts/check_webhook.sh

set_webhook:  ## Set this bot webhook to google cloud function
	bash scripts/set_webhook.sh

set_webhook_local:  ## Set webhook to local
	bash scripts/set_webhook_local.sh

serve_function_local: ## Serve google cloud function locally
	bash scripts/serve_function_local.sh

serve_aiogram: ## Serve aiogram bot locally
	python main_aiogram.py

serve_fastapi: ## Serve fastapi bot locally
	python main_fastapi.py
