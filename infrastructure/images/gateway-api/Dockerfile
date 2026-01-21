# Retrieve the python version from build arguments, deliberately set to "invalid" by default to highlight when no version is provided when building the container.
ARG PYTHON_VERSION=invalid
FROM python:${PYTHON_VERSION}-slim AS gateway-api

COPY resources/ /resources

WORKDIR /resources/build/gateway-api

ENV PYTHONPATH=/resources/build/gateway-api
ENV FLASK_HOST="0.0.0.0"
ENV FLASK_PORT="8080"

ARG COMMIT_VERSION
ENV COMMIT_VERSION=$COMMIT_VERSION
ARG BUILD_DATE
ENV BUILD_DATE=$BUILD_DATE

ENTRYPOINT ["python"]
CMD ["gateway_api/app.py"]

