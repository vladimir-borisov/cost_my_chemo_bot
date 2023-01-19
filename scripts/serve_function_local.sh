#!env /bin/bash
set -euxo pipefail
functions-framework --target process_webhook --port 8080
