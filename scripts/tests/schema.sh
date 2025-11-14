#!/bin/bash

set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

cd gateway-api
mkdir -p test-artifacts
poetry run pytest tests/schema/ -v \
  --cov=src/gateway_api \
  --cov-report=html:test-artifacts/coverage-html \
  --cov-report=term \
  --junit-xml=test-artifacts/schema-tests.xml \
  --html=test-artifacts/schema-tests.html --self-contained-html
# Save coverage data file for merging
mv .coverage test-artifacts/coverage.schema
