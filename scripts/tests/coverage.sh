#!/bin/bash

set -e

cd gateway-api

# Create coverage directory
mkdir -p test-artifacts/coverage

# Copy all coverage data files
cp test-artifacts/unit/.coverage.unit test-artifacts/coverage/
cp test-artifacts/contract/.coverage.contract test-artifacts/coverage/
cp test-artifacts/schema/.coverage.schema test-artifacts/coverage/

# Merge coverage data
cd test-artifacts/coverage
poetry run coverage combine

# Generate reports
poetry run coverage report
poetry run coverage html -d html
