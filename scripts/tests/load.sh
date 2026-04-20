#!/bin/bash

set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel)"

# Load environment variables from .env if it exists
if [[ -f "$ROOT_DIR/.env" ]]; then
    set -a
    source "$ROOT_DIR/.env"
    set +a
fi

if [[ -z "${BASE_URL:-}" ]]; then
    echo "BASE_URL not set"
    exit 1
else
    echo "Running load tests against host: $BASE_URL"
fi

cd "$ROOT_DIR/gateway-api"

if [[ "${UI:-false}" == "true" ]]; then
    poetry run locust -f tests/load/ -u 10 -r 1 -t 10s --host "$BASE_URL"
else
    mkdir -p "test-artefacts"
    poetry run locust -f tests/load/ --headless -u 10 -r 1 -t 10s --host "$BASE_URL" --csv "test-artefacts/load-tests" --html "test-artefacts/load-tests.html"
fi
