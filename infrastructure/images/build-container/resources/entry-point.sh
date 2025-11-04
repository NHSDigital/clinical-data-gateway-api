#!/bin/bash

set -e

if [ $DEV_CERTS_INCLUDED = "true" ]; then
  docker buildx stop gateway-builder || true
  docker buildx rm gateway-builder || true

  docker buildx create --use --bootstrap \
      --name gateway-builder \
      --driver docker-container \
      --buildkitd-config /etc/buildkitd.toml
fi

sleep infinity
