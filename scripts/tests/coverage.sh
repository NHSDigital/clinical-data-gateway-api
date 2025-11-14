#!/bin/bash

set -e

cd gateway-api

# Create coverage directory
mkdir -p test-artifacts/coverage

# Copy all coverage data files from downloaded artifacts
cp unit-test-results/coverage.unit test-artifacts/coverage/
cp contract-test-results/coverage.contract test-artifacts/coverage/
cp schema-test-results/coverage.schema test-artifacts/coverage/
cp integration-test-results/coverage.integration test-artifacts/coverage/

# Merge coverage data
cd test-artifacts/coverage
# Rename files to .coverage.* format that coverage combine expects
mv coverage.unit .coverage.unit
mv coverage.contract .coverage.contract
mv coverage.schema .coverage.schema
mv coverage.integration .coverage.integration
# Go back to project root for coverage operations
cd ../..
poetry run coverage combine test-artifacts/coverage

# Generate reports
poetry run coverage report
poetry run coverage xml -o test-artifacts/coverage/coverage-merged.xml
# Fix paths in XML to be relative to repository root
sed -i 's#filename="src/#filename="gateway-api/src/#g' test-artifacts/coverage/coverage-merged.xml
