#!/usr/bin/env bash

PROXYGEN_PTL_DIR="$HOME/gateway/ptl/.proxygen"

# Ensure the host ptl directory exists
mkdir -p "$PROXYGEN_PTL_DIR"

# Loop through templates and copy if the settings or credentials files don't exist
for f in proxygen/*s.template.yaml; do
    if [[ -f "$f" ]]; then
        destination="$PROXYGEN_PTL_DIR/$(basename "$f" | sed 's/.template//')"
        if [[ ! -f "$destination" ]]; then
            cp "$f" "$destination"
        fi
    fi
done
