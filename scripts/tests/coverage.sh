#!/bin/bash

set -e

cd gateway-api

# Create coverage directory
mkdir -p test-artifacts/coverage

# Copy all coverage data files from downloaded artifacts
# Each artifact is downloaded to gateway-api/{unit,contract,schema}/
# and contains test-artifacts/ from the upload
cp unit/test-artifacts/.coverage.unit test-artifacts/coverage/
cp contract/test-artifacts/.coverage.contract test-artifacts/coverage/
cp schema/test-artifacts/.coverage.schema test-artifacts/coverage/

# Merge coverage data
cd test-artifacts/coverage
poetry run coverage combine

# Generate reports
poetry run coverage report
poetry run coverage html -d html
