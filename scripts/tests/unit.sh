#!/bin/bash

set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

cd gateway-api
mkdir -p test-artifacts
poetry run pytest tests/unit/ -v \
  --junit-xml=test-artifacts/unit-tests.xml \
  --html=test-artifacts/unit-tests.html --self-contained-html
