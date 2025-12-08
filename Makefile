# This file is for you! Edit it to implement your own hooks (make targets) into
# the project as automated steps to be executed on locally and in the CD pipeline.

include scripts/init.mk

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
	@pip install "dist/gateway_api-0.1.0-py3-none-any.whl" --target "./target/gateway-api"
	# Copy main file separately as it is not included within the package.
	@cp lambda_handler.py ./target/gateway-api/
	@rm -rf ../infrastructure/images/gateway-api/resources/build/
	@mkdir ../infrastructure/images/gateway-api/resources/build/
	@cp -r ./target/gateway-api ../infrastructure/images/gateway-api/resources/build/

.PHONY: build
build: build-gateway-api # Build the project artefact @Pipeline
	@echo "Building Docker image using Docker..."
	@docker buildx build --load --provenance=false -t localhost/gateway-api-image infrastructure/images/gateway-api
	@echo "Docker image 'gateway-api-image' built successfully!"

publish: # Publish the project artefact @Pipeline
	# TODO: Implement the artefact publishing step

deploy: clean build # Deploy the project artefact to the target environment @Pipeline
	@docker run --name gateway-api -p 5000:8080 -d localhost/gateway-api-image

clean:: stop # Clean-up project resources (main) @Operations
	@echo "Removing Gateway API container..."
	@docker rm gateway-api || echo "No Gateway API container currently exists."

.PHONY: stop
stop:
	@echo "Stopping Gateway API container..."
	@docker stop gateway-api || echo "No Gateway API container currently running."

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
