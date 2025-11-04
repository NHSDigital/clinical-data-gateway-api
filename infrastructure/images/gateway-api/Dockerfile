# Base image
FROM python:3.13.9-alpine3.22

COPY resources/ /resources

RUN mkdir /app
WORKDIR /app

COPY /resources/build/gateway-api .

ENTRYPOINT ["sleep", "infinity"]
