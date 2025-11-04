#!/bin/sh

set -e

TEMPLATE="/resources/buildkitd.toml.temp"
DIR="/etc/ssl/certs/*.crt"

# Collect file names in the directory, separated by commas
FILES=$(find $DIR -type f -exec echo \"{}\" \; | tr '\n' ',')

# Replace the placeholder {{CERTS}} in the template with the file list
sed "s|{{CERTS}}|$FILES|g" "$TEMPLATE" > "/etc/buildkitd.toml"
