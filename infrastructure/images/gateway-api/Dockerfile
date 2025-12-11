# Retrieve the python version from build arguments, deliberately set to "invalid" by default to highlight when no version is provided when building the container.
ARG PYTHON_VERSION=invalid
# Use the specified python version to retrieve the required base lambda image.
ARG url=public.ecr.aws/lambda/python:${PYTHON_VERSION}
FROM $url

COPY resources/ /resources

COPY /resources/build/gateway-api ${LAMBDA_TASK_ROOT}

CMD [ "lambda_handler.handler" ]
