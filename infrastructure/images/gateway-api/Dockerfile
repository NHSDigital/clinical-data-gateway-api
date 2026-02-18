# Retrieve the python version from build arguments, deliberately set to "invalid" by default to highlight when no version is provided when building the container.
ARG PYTHON_VERSION=invalid
FROM python:${PYTHON_VERSION}-alpine3.23 AS gateway-api

RUN addgroup -S nonroot \
    && adduser -S gateway_api_user -G nonroot

COPY resources/ /resources

WORKDIR /resources/build/gateway-api

ENV PYTHONPATH=/resources/build/gateway-api
ENV FLASK_HOST="0.0.0.0"
ENV FLASK_PORT="8080"

# Configure external services to use stubs
# To disable, comment these out - if they're set at all, it'll use the stub
ENV STUB_SDS=true
ENV STUB_PDS=true
ENV STUB_PROVIDER=true

ARG COMMIT_VERSION
ENV COMMIT_VERSION=$COMMIT_VERSION
ARG BUILD_DATE
ENV BUILD_DATE=$BUILD_DATE

USER gateway_api_user
ENTRYPOINT ["python"]
CMD ["gateway_api/app.py"]

