#!/bin/bash

set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

cd gateway-api
mkdir -p test-artifacts
poetry run pytest tests/contract/ -v \
  --junit-xml=test-artifacts/contract-tests.xml \
  --html=test-artifacts/contract-tests.html --self-contained-html
