#!/bin/bash

set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

cd gateway-api
mkdir -p test-artefacts
poetry run pytest tests/acceptance/ -v \
  --cov=src/gateway_api \
  --cov-report=html:test-artefacts/coverage-html \
  --cov-report=term \
  --junit-xml=test-artefacts/acceptance-tests.xml \
  --html=test-artefacts/acceptance-tests.html --self-contained-html
# Save coverage data file for merging
mv .coverage test-artefacts/coverage.acceptance
