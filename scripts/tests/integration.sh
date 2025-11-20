#!/bin/bash

set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

cd gateway-api
mkdir -p test-artefacts
poetry run coverage run -m behave --junit --junit-directory test-artefacts -f behave_html_pretty_formatter:PrettyHTMLFormatter -o test-artefacts/integration-tests.html
# Save coverage data file for merging
mv .coverage test-artefacts/coverage.integration
