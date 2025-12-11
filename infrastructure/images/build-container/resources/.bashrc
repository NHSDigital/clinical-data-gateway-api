# Add pyenv to the path.
export PYENV_ROOT="/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"

# Add asdf and its plugins to the path.
export PATH="/asdf:$PATH"
export ASDF_DATA_DIR="/.asdf"
export PATH="${ASDF_DATA_DIR:-$HOME/.asdf}/shims:$PATH"

# Add pipx binaries to the path.
export PATH="/pipx/bin:$PATH"

# Initialize pyenv
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

# Auto-activate gateway environment
pyenv shell gateway 2>/dev/null || true

alias docker="doas docker"
