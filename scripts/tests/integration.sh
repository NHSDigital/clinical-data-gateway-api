#!/bin/bash

set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

cd gateway-api
mkdir -p test-artifacts
poetry run behave --junit --junit-directory test-artifacts -f behave_html_pretty_formatter:PrettyHTMLFormatter -o test-artifacts/integration-tests.html
