#!/bin/bash

set -euo pipefail

# Generic test runner script
# Usage: run-test.sh <test-type>
# Where test-type is one of: unit, integration, contract, schema, acceptance


if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <test-type>"
  echo "Where test-type is one of: unit, integration, contract, schema, acceptance"
  exit 1
fi

TEST_TYPE="$1"

# Validate test type early
if [[ ! "$TEST_TYPE" =~ ^(unit|integration|contract|schema|acceptance)$ ]]; then
  echo "Error: Unknown test type '$TEST_TYPE'" >&2
  echo "Valid types are: unit, integration, contract, schema, acceptance" >&2
  exit 1
fi

cd "$(git rev-parse --show-toplevel)"

# Determine test path based on test type
if [[ "$TEST_TYPE" = "unit" ]]; then
  TEST_PATH="src"
else
  TEST_PATH="tests/${TEST_TYPE}/"
fi

source .env.test
if [[ "$TEST_TYPE" = "unit" ]]; then
  set -a
  source .env
  set +a
fi

cd gateway-api
mkdir -p test-artefacts

echo "Running ${TEST_TYPE} tests..."

# Set coverage path based on test type
if [[ "$TEST_TYPE" = "unit" ]]; then
  COV_PATH="."
else
  COV_PATH="src/gateway_api"
fi

# TODO: Add some logging to prove which URLS are being hit
poetry run pytest ${TEST_PATH} -v \
  --api-name="${PROXYGEN_API_NAME}" \
  --proxy-name="${PROXYGEN_API_NAME}--internal-dev--${PROXY_BASE_PATH}" \
  --cov="${COV_PATH}" \
  --cov-report=html:test-artefacts/coverage-html \
  --cov-report=term \
  --junit-xml="test-artefacts/${TEST_TYPE}-tests.xml" \
  --html="test-artefacts/${TEST_TYPE}-tests.html" --self-contained-html

# Save coverage data file for merging
mv .coverage "test-artefacts/coverage.${TEST_TYPE}"
