FROM docker:28.5.0-cli AS gateway-build-container

ENV IN_BUILD_CONTAINER=true
ENV ASDF_DOWNLOAD_URL="https://github.com/asdf-vm/asdf/releases/download/v0.18.0/"

ARG PYTHON_VERSION
ARG INCLUDE_DEV_CERTS

COPY resources/ /resources

# Install required certificates for dev machines.
RUN if [ "$INCLUDE_DEV_CERTS" = "true" ] ; then \
    cp -r /resources/dev-certificates/* /usr/local/share/ca-certificates/; \
    apk --no-cache add --no-check-certificate ca-certificates \
        && update-ca-certificates; \
else \
    rm -r /resources/dev-certificates; \
fi

RUN apk update

RUN apk add --no-cache --update bash \
    curl \
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

# Install Python (via pyenv)
RUN curl -fsSL https://pyenv.run | bash

RUN /root/.pyenv/bin/pyenv install ${PYTHON_VERSION}
RUN /root/.pyenv/bin/pyenv global ${PYTHON_VERSION}

COPY /resources/.bashrc /root/.bashrc

# Install asdf via Go to configure plugins,
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

WORKDIR /resources
# Run install other development plugins via asdf.
RUN bash -c "source /root/.bashrc && bash ./install-asdf-plugins.sh"

# Install pipx and poetry
RUN bash -c "source /root/.bashrc && pip install --root-user-action ignore pipx && pipx install poetry"

# Create a virtual environment for development
RUN bash -c "source /root/.bashrc && pyenv virtualenv ${PYTHON_VERSION} gateway"

WORKDIR /git

ENTRYPOINT ["sleep", "infinity"]