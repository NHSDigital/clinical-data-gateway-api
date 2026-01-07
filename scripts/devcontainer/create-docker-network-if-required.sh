#!/bin/bash

set -e

docker network create gateway-local || echo "Local network already exists"
