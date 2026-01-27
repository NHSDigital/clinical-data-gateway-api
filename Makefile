# This file is for you! Edit it to implement your own hooks (make targets) into
# the project as automated steps to be executed on locally and in the CD pipeline.

include scripts/init.mk

# Within the build container the `doas` command is required when running docker commands as we're running as a non-root user.
ifeq (${IN_BUILD_CONTAINER}, true)
docker := doas docker
else
docker := docker
endif

IMAGE_REPOSITORY ?= localhost/gateway-api-image
IMAGE_TAG ?= latest

ifdef ECR_URL
IMAGE_REPOSITORY := ${ECR_URL}
endif

IMAGE_NAME := ${IMAGE_REPOSITORY}:${IMAGE_TAG}
COMMIT_VERSION := $(shell git rev-parse --short HEAD)
BUILD_DATE := $(shell date -u +"%Y%m%d")
# ==============================================================================

# Example CI/CD targets are: dependencies, build, publish, deploy, clean, etc.

.PHONY: dependencies
dependencies: # Install dependencies needed to build and test the project @Pipeline
	cd gateway-api && poetry sync

.PHONY: build-gateway-api
build-gateway-api: dependencies
	@cd gateway-api
	@echo "Running type checks..."
	@rm -rf target && rm -rf dist
	@poetry run mypy --no-namespace-packages .
	@echo "Packaging dependencies..."
	@poetry build --format=wheel
	@pip install "dist/gateway_api-0.1.0-py3-none-any.whl" --target "./target/gateway-api" --platform musllinux_1_2_x86_64 --only-binary=:all:
	# Copy main file separately as it is not included within the package.
	@rm -rf ../infrastructure/images/gateway-api/resources/build/
	@mkdir ../infrastructure/images/gateway-api/resources/build/
	@cp -r ./target/gateway-api ../infrastructure/images/gateway-api/resources/build/
	# Remove temporary build artefacts once build has completed
	@rm -rf target && rm -rf dist

.PHONY: build
build: build-gateway-api # Build the project artefact @Pipeline
	@echo "Building Docker x86 image using Docker. Utilising python version: ${PYTHON_VERSION} ..."
	@$(docker) buildx build --platform linux/amd64 --load --provenance=false --build-arg PYTHON_VERSION=${PYTHON_VERSION} --build-arg COMMIT_VERSION=${COMMIT_VERSION} --build-arg BUILD_DATE=${BUILD_DATE} -t ${IMAGE_NAME} infrastructure/images/gateway-api
	@echo "Docker image '${IMAGE_NAME}' built successfully!"

publish: # Publish the project artefact @Pipeline
	# TODO: Implement the artefact publishing step

deploy: clean build # Deploy the project artefact to the target environment @Pipeline
	@if [[ -n "$${IN_BUILD_CONTAINER}" ]]; then \
		echo "Starting using local docker network ..." ; \
		$(docker) run --platform linux/amd64 --name gateway-api -p 5000:8080 --network gateway-local -d ${IMAGE_NAME} ; \
	else \
		$(docker) run --platform linux/amd64 --name gateway-api -p 5000:8080 -d ${IMAGE_NAME} ; \
	fi

clean:: stop # Clean-up project resources (main) @Operations
	@echo "Removing Gateway API container..."
	@$(docker) rm gateway-api || echo "No Gateway API container currently exists."

.PHONY: stop
stop:
	@echo "Stopping Gateway API container..."
	@$(docker) stop gateway-api || echo "No Gateway API container currently running."

config:: # Configure development environment (main) @Configuration
	# Configure poetry to trust dev certificate if specified
	@if [[ -n "$${DEV_CERTS_INCLUDED}" ]]; then \
		echo "Configuring poetry to trust the dev certificate..."  ; \
		poetry config certificates.PyPI.cert /etc/ssl/cert.pem ; \
	fi
	make _install-dependencies

# ==============================================================================

${VERBOSE}.SILENT: \
	build \
	clean \
	config \
	dependencies \
	deploy \
