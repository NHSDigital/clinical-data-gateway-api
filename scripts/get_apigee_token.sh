#!/usr/bin/env bash
set -euo pipefail

# Generates an APIGEE access token for remote test runs.
# Prints only the token to stdout; all diagnostics go to stderr.
#
# Prerequisites:
#   - proxygen CLI installed and configured (credentials in ~/.proxygen/credentials.yaml)
#   - jq installed
#   - Valid proxygen key (PROXYGEN_KEY_ID / PROXYGEN_CLIENT_ID env vars or config)
#
# The token is valid for ~24 hours and is a secret — do not log it.

echo "Generating APIGEE access token via proxygen..." >&2

TOKEN=$(proxygen pytest-nhsd-apim get-token | jq -r '.pytest_nhsd_apim_token')

if [[ -z "${TOKEN}" || "${TOKEN}" == "null" ]]; then
  echo "ERROR: Failed to obtain a valid token." >&2
  exit 1
fi

echo "Token obtained successfully." >&2
echo "${TOKEN}"
