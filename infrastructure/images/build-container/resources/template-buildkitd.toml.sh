#!/bin/sh

set -e

TEMPLATE="/resources/buildkitd.toml.temp"

# Replace the placeholder {{CERTS}} in the template with the defined dev cert path.
sed "s|{{CERTS}}|\"$DEV_CERT_PATH\"|g" "$TEMPLATE" > "/etc/buildkitd.toml"
