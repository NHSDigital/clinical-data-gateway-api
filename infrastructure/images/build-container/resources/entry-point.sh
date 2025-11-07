#!/bin/bash

set -e

if [ $DEV_CERTS_INCLUDED = "true" ]; then
  echo "Adding dev certificates to buildkit..."
  docker stop buildx_buildkit_gateway-builder0 || true
  docker rm buildx_buildkit_gateway-builder0 || true

  docker buildx create --use --bootstrap \
      --name gateway-builder \
      --driver docker-container \
      --buildkitd-config /etc/buildkitd.toml
fi

sleep infinity
