# Retrieve the python version from build arguments, deliberately set to "invalid" by default to highlight when no version is provided when building the container.
ARG PYTHON_VERSION=invalid
FROM python:${PYTHON_VERSION}-alpine3.23 AS gateway-api


COPY resources/ /resources

# Check for at least one .crt file in /resources/dev-certificates before installing certificates
RUN if ! ls /resources/dev-certificates/*.crt 1> /dev/null 2>&1; then \
    echo "ERROR: No .crt files found in /resources/dev-certificates."; \
    exit 1; \
fi

# Install required certificates for dev machines and upgrade packages.
RUN cp -r /resources/dev-certificates/* /usr/local/share/ca-certificates/; \
    update-ca-certificates; \
    cp -r /resources/dev-certificates/* /etc/ssl/certs/; \
    apk upgrade --no-cache; \
    addgroup -S nonroot; \
    adduser -S gateway_api_user -G nonroot


WORKDIR /resources/build/gateway-api

ENV PYTHONPATH=/resources/build/gateway-api
ENV FLASK_HOST="0.0.0.0"
ENV FLASK_PORT="8080"
ENV STUB_PDS="true"
ENV STUB_PROVIDER="true"
ENV STUB_SDS="true"

ARG COMMIT_VERSION
ENV COMMIT_VERSION=$COMMIT_VERSION
ARG BUILD_DATE
ENV BUILD_DATE=$BUILD_DATE

USER gateway_api_user
ENTRYPOINT ["python"]
CMD ["gateway_api/app.py"]

