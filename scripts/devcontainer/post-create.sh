#!/bin/bash

set -e

echo "Configuring zsh..."

echo 'export GPG_TTY=$TTY' | cat - ~/.zshrc > temp && mv temp ~/.zshrc
echo 'source ~/.bashrc' >> ~/.zshrc

echo "zsh configuration completed."
