# Retrieve the python version from build arguments, deliberately set to "invalid" by default to highlight when no version is provided when building the container.
ARG PYTHON_VERSION=invalid
FROM python:${PYTHON_VERSION}-alpine3.23 AS gateway-api

COPY resources/ /resources

RUN apk upgrade --no-cache && \
    pip install --no-cache-dir --upgrade pip && \
    addgroup -S nonroot && \
    adduser -S gateway_api_user -G nonroot

WORKDIR /resources/build/gateway-api

ENV PYTHONPATH=/resources/build/gateway-api
ENV FLASK_HOST="0.0.0.0"
ENV FLASK_PORT="8080"

ENV APIM_API_KEY="default_api_key"
ENV APIM_TOKEN_EXPIRY_THRESHOLD="30s"
ENV APIM_KEY_ID="default_key_id"
ENV APIM_PRIVATE_KEY="default_private_key"
ENV CLIENT_TIMEOUT=30s

ARG COMMIT_VERSION
ENV COMMIT_VERSION=$COMMIT_VERSION
ARG BUILD_DATE
ENV BUILD_DATE=$BUILD_DATE

USER gateway_api_user
ENTRYPOINT ["python"]
CMD ["gateway_api/app.py"]
