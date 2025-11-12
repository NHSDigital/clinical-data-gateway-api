#!/bin/bash

set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

cd gateway-api
mkdir -p test-artifacts
poetry run pytest tests/schema/ -v \
  --junit-xml=test-artifacts/schema-tests.xml \
  --html=test-artifacts/schema-tests.html --self-contained-html
