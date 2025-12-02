#!/bin/bash

set -e

# Merge coverage data
cd gateway-api/test-artefacts
# Rename files to .coverage.* format that coverage combine expects
mv unit-test-results/coverage.unit .coverage.unit
mv contract-test-results/coverage.contract .coverage.contract
mv schema-test-results/coverage.schema .coverage.schema
mv integration-test-results/coverage.integration .coverage.integration
mv acceptance-test-results/coverage.acceptance .coverage.acceptance
# Go back to project root for coverage operations
cd ..
poetry run coverage combine test-artefacts

# Generate reports
poetry run coverage report
poetry run coverage xml -o test-artefacts/coverage-merged.xml
# Fix paths in XML to be relative to repository root
sed -i 's#filename="src/#filename="gateway-api/src/#g' test-artefacts/coverage-merged.xml
