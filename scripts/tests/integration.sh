#!/bin/bash

set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

cd gateway-api
mkdir -p test-artifacts
poetry run coverage run -m behave --junit --junit-directory test-artifacts -f behave_html_pretty_formatter:PrettyHTMLFormatter -o test-artifacts/integration-tests.html
# Save coverage data file for merging
mv .coverage test-artifacts/coverage.integration
