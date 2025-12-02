#!/bin/bash

set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

./scripts/tests/run-test.sh integration
