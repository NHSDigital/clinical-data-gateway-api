#!/bin/bash

set -e

cd gateway-api

# Create coverage directory
mkdir -p test-artefacts/coverage

# Copy all coverage data files from downloaded artefacts
cp unit-test-results/coverage.unit test-artefacts/coverage/
cp contract-test-results/coverage.contract test-artefacts/coverage/
cp schema-test-results/coverage.schema test-artefacts/coverage/
cp integration-test-results/coverage.integration test-artefacts/coverage/
cp acceptance-test-results/coverage.acceptance test-artefacts/coverage/

# Merge coverage data
cd test-artefacts/coverage
# Rename files to .coverage.* format that coverage combine expects
mv coverage.unit .coverage.unit
mv coverage.contract .coverage.contract
mv coverage.schema .coverage.schema
mv coverage.integration .coverage.integration
mv coverage.acceptance .coverage.acceptance
# Go back to project root for coverage operations
cd ../..
poetry run coverage combine test-artefacts/coverage

# Generate reports
poetry run coverage report
poetry run coverage xml -o test-artefacts/coverage/coverage-merged.xml
# Fix paths in XML to be relative to repository root
sed -i 's#filename="src/#filename="gateway-api/src/#g' test-artefacts/coverage/coverage-merged.xml
