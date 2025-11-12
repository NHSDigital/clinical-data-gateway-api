#!/bin/bash

set -e

cd gateway-api

# Create coverage directory
mkdir -p test-artifacts/coverage

# Copy all coverage data files from downloaded artifacts
# Artifacts uploaded from gateway-api/test-artifacts/ are downloaded directly to unit/, contract/, schema/
cp unit/.coverage.unit test-artifacts/coverage/
cp contract/.coverage.contract test-artifacts/coverage/
cp schema/.coverage.schema test-artifacts/coverage/

# Merge coverage data
cd test-artifacts/coverage
poetry run coverage combine

# Generate reports
poetry run coverage report
poetry run coverage html -d html
