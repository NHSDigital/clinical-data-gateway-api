#!/bin/zsh

set -e

echo "Running post-create script..."

echo "export GPG_TTY=$TTY" | cat - ~/.zshrc > temp && mv temp ~/.zshrc
echo "source ~/.bashrc" >> ~/.zshrc

echo "Post-create script completed."
