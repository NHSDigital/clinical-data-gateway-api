#!/bin/bash

set -e

cd gateway-api

# Create coverage directory
mkdir -p test-artifacts/coverage

# Debug: List downloaded artifacts
echo "Listing downloaded artifact directories:"
ls -la unit/ contract/ schema/ || true

# Copy all coverage data files from downloaded artifacts
# Artifacts uploaded from gateway-api/test-artifacts/ are downloaded directly to unit/, contract/, schema/
cp unit/coverage.unit test-artifacts/coverage/
cp contract/coverage.contract test-artifacts/coverage/
cp schema/coverage.schema test-artifacts/coverage/

# Merge coverage data
cd test-artifacts/coverage
# Rename files to .coverage.* format that coverage combine expects
mv coverage.unit .coverage.unit
mv coverage.contract .coverage.contract
mv coverage.schema .coverage.schema
poetry run coverage combine

# Generate reports
poetry run coverage report
poetry run coverage html -d html
