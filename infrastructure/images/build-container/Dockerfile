FROM mcr.microsoft.com/vscode/devcontainers/base:alpine-3.22 AS gateway-build-container

ENV PYTHON_VERSION="3.14"

ENV ASDF_DOWNLOAD_URL="https://github.com/asdf-vm/asdf/releases/download/v0.18.0/"
ENV EDITORCONFIG_DOWNLOAD_URL="https://github.com/editorconfig-checker/editorconfig-checker/releases/download/v3.4.1/"

ARG INCLUDE_DEV_CERTS
ARG DEV_CERT_FILENAME

# Add development certificates to node if provided.
ENV NODE_EXTRA_CA_CERTS=${INCLUDE_DEV_CERTS:+/etc/ssl/certs/ca-certificates.crt}
ENV DEV_CERTS_INCLUDED=$INCLUDE_DEV_CERTS

ENV IN_BUILD_CONTAINER=true

COPY resources/ /resources

# Install required certificates for dev machines.
RUN if [ "$INCLUDE_DEV_CERTS" = "true" ] ; then \
    cp -r /resources/dev-certificates/* /usr/local/share/ca-certificates/; \
    update-ca-certificates; \

    cp -r /resources/dev-certificates/* /etc/ssl/certs/; \
else \
    rm -r /resources/dev-certificates; \
fi

RUN apk update

RUN apk add --no-cache --update bash \
    # Required to manage user permissions.
    doas \
    shadow \
    curl \
    # Required to validate english usage in prose/comments.
    vale \
    # Required to support markdownlint-cli installation.
    npm \
    # Required to support the building of other docker images.
    docker-cli \
    docker-cli-buildx \
    # pyenv suggested requirements taken from https://github.com/pyenv/pyenv/wiki#suggested-build-environment
    build-base \
    libffi-dev \
    openssl-dev \
    bzip2-dev \
    zlib-dev \
    xz-dev \
    readline-dev \
    sqlite-dev \
    tk-dev \
    zstd-dev

# Configure doas to allow members of the wheel group to run commands as root.
RUN echo "permit :wheel" >> /etc/doas.conf \
    && echo "permit nopass :wheel as root cmd apk" >> /etc/doas.conf \
    && echo "permit nopass :wheel as root cmd docker" >> /etc/doas.conf \
    # Change default shell to bash for root user.
    && chsh -s /bin/bash root

# Ensure pyenv is on the PATH
ENV PYENV_ROOT="/.pyenv"
ENV PATH="$PYENV_ROOT/bin:$PATH"

# Install Python (via pyenv)
RUN curl -fsSL https://pyenv.run | bash

RUN /.pyenv/bin/pyenv install ${PYTHON_VERSION}
RUN /.pyenv/bin/pyenv global ${PYTHON_VERSION}

# Initialise pyenv for use.
RUN /.pyenv/bin/pyenv init -

COPY /resources/.bashrc /root/.bashrc

# Install asdf to configure plugins.
RUN mkdir "/.asdf"
ENV ASDF_DATA_DIR="/.asdf"

RUN mkdir /asdf
WORKDIR /asdf

# If we're running on an arm64 architecture download the arm64 executeable.
RUN if [ "$(uname -m)" = "aarch64" ] ; then \
    echo "Installing ARM asdf executable..." ; \
    wget -O asdf.tar.gz "$ASDF_DOWNLOAD_URL/asdf-v0.18.0-linux-arm64.tar.gz"; \
else \
    echo "Installing x86 asdf executable..." ; \
    wget -O asdf.tar.gz "$ASDF_DOWNLOAD_URL/asdf-v0.18.0-linux-amd64.tar.gz"; \
fi

RUN tar -xvf asdf.tar.gz

# Install editorconfig-checker to validate formatting.
RUN mkdir /editorconfig
WORKDIR /editorconfig

RUN if [ "$(uname -m)" = "aarch64" ] ; then \
    echo "Installing ARM editorconfig..." ; \
    wget -O editorconfig.tar.gz "$EDITORCONFIG_DOWNLOAD_URL/ec-linux-arm64.tar.gz"; \
    tar -xvf editorconfig.tar.gz; \
    mv bin/ec-linux-arm64 /usr/local/bin/editorconfig; \
else \
    echo "Installing x86 editorconfig..." ; \
    wget -O editorconfig.tar.gz "$EDITORCONFIG_DOWNLOAD_URL/ec-linux-amd64.tar.gz"; \
    tar -xvf editorconfig.tar.gz; \
    mv bin/ec-linux-amd64 /usr/local/bin/editorconfig; \
fi

# Ensure asdf is on the PATH
ENV PATH="/asdf:$PATH"
ENV PATH="$ASDF_DATA_DIR/shims:$PATH"

WORKDIR /resources
# Run install other development plugins via asdf.
RUN bash "./install-asdf-plugins.sh"

WORKDIR /workspace/clinical-data-gateway-api

# Install pipx and poetry
ENV PIPX_BIN_DIR="/pipx/bin"
ENV PIPX_HOME="/pipx/lib"
RUN bash -c "source ~/.bashrc && pip install --root-user-action ignore pipx && pipx install poetry && pipx install ruff"
ENV PATH="$PIPX_BIN_DIR:$PATH"

# Create a virtual environment for development
RUN bash -c "source ~/.bashrc && pyenv virtualenv ${PYTHON_VERSION} gateway" \
    # Install markdownlint-cli
    && npm install -g --ignore-scripts markdownlint-cli \
    && export PATH \
    && addgroup dev \

    # Allow access to pyenv tools for dev users.
    && chown -R root:dev /.pyenv \
    && chmod -R g+w /.pyenv \

    # Allow access to asdf tools for dev users.
    && chown -R root:dev /.asdf \
    && chmod -R g+w /.asdf \

    # Create a new user based on the default vscode user.
    && groupmod -n gateway-dev vscode \
    && usermod -l gateway-dev -d /home/gateway-dev -m vscode \
    && addgroup gateway-dev dev \
    && addgroup gateway-dev wheel \

    # Change default shell to bash for gateway-dev user.
    && chsh -s /bin/bash gateway-dev

# Update gateway-dev user's bash configuration.
COPY /resources/.bashrc /home/gateway-dev/.bashrc

USER gateway-dev
