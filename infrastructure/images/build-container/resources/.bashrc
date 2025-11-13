# Add pyenv to the path.
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

# Add pipx applications to the path.
export PATH="$PATH:/root/.local/bin"

# Add asdf and its plugins to the path.
export PATH="/asdf:$PATH"
export PATH="${ASDF_DATA_DIR:-$HOME/.asdf}/shims:$PATH"

# Initialize pyenv
eval "$(pyenv init -)"

# Auto-activate gateway environment
pyenv shell gateway 2>/dev/null || true
