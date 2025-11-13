#!/bin/bash

set -e

cd gateway-api

# Create coverage directory
mkdir -p test-artifacts/coverage

# Copy all coverage data files from downloaded artifacts
cp unit/coverage.unit test-artifacts/coverage/
cp contract/coverage.contract test-artifacts/coverage/
cp schema/coverage.schema test-artifacts/coverage/

# Merge coverage data
cd test-artifacts/coverage
# Rename files to .coverage.* format that coverage combine expects
mv coverage.unit .coverage.unit
mv coverage.contract .coverage.contract
mv coverage.schema .coverage.schema
# Go back to project root for coverage operations
cd ../..
poetry run coverage combine test-artifacts/coverage

# Generate reports
poetry run coverage report
poetry run coverage xml -o test-artifacts/coverage/coverage-merged.xml
poetry run coverage html -d test-artifacts/coverage/coverage-merged-html
