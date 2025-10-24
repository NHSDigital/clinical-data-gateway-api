# Add pyenv to the path.
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init - bash)"
eval "$(pyenv virtualenv-init -)"

# Add pipx applications to the path.
export PATH="$PATH:/root/.local/bin"

# Add go programs to the path.
export PATH=$PATH:$(go env GOPATH)/bin

# Add asdf plugins to the path.
export PATH="${ASDF_DATA_DIR:-$HOME/.asdf}/shims:$PATH"