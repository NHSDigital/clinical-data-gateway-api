#!/bin/bash

confirm_overwrite() {
    local file="$1"
    if [ -f "$file" ]; then
        printf "'%s' already exists. Overwrite? [y/N]: " "$file"
        read -r answer
        case "$answer" in
            [yY]|[yY][eE][sS])
                echo "Overwriting $file..."
                ;;
            *)
                echo "Aborted."
                exit 0
                ;;
        esac
    fi
}
