#!/bin/bash

set -euo pipefail

# Generic test runner script
# Usage: run-test.sh <test-type>
# Where test-type is one of: unit, integration, contract, schema, acceptance

if [ $# -ne 1 ]; then
  echo "Usage: $0 <test-type>"
  echo "Where test-type is one of: unit, integration, contract, schema, acceptance"
  exit 1
fi

TEST_TYPE="$1"

# Validate test type early
if [[ ! "$TEST_TYPE" =~ ^(unit|integration|contract|schema|acceptance)$ ]]; then
  echo "Error: Unknown test type '$TEST_TYPE'"
  echo "Valid types are: unit, integration, contract, schema, acceptance"
  exit 1
fi

cd "$(git rev-parse --show-toplevel)"

# Determine test path based on test type
if [ "$TEST_TYPE" = "unit" ]; then
  TEST_PATH="src/*/test_*.py"
else
  TEST_PATH="tests/${TEST_TYPE}/"
fi

cd gateway-api
mkdir -p test-artefacts

echo "Running ${TEST_TYPE} tests..."

# Note: TEST_PATH is intentionally unquoted to allow glob expansion for unit tests
poetry run pytest ${TEST_PATH} -v \
  --cov=src/gateway_api \
  --cov-report=html:test-artefacts/coverage-html \
  --cov-report=term \
  --junit-xml="test-artefacts/${TEST_TYPE}-tests.xml" \
  --html="test-artefacts/${TEST_TYPE}-tests.html" --self-contained-html

# Save coverage data file for merging
mv .coverage "test-artefacts/coverage.${TEST_TYPE}"
