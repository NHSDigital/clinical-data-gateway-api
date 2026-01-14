# Retrieve the python version from build arguments, deliberately set to "invalid" by default to highlight when no version is provided when building the container.
ARG PYTHON_VERSION=invalid
FROM python:${PYTHON_VERSION}-slim AS gateway-api

COPY resources/ /resources

WORKDIR /resources/build/gateway-api

ENV PYTHONPATH=/resources/build/gateway-api

ENTRYPOINT ["python"]
CMD ["gateway_api/app.py"]

