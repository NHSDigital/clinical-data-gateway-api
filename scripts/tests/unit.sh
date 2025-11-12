#!/bin/bash

set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

cd gateway-api
poetry run pytest tests/unit/ -v

echo "Unit tests are not yet implemented. See scripts/tests/unit.sh for more."
