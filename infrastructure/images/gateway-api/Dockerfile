# Base image
FROM public.ecr.aws/lambda/python:3.14

COPY resources/ /resources

COPY /resources/build/gateway-api ${LAMBDA_TASK_ROOT}

CMD [ "lambda_handler.handler" ]
