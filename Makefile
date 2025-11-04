# This file is for you! Edit it to implement your own hooks (make targets) into
# the project as automated steps to be executed on locally and in the CD pipeline.

ifeq (${IN_BUILD_CONTAINER},true)
include scripts/init.mk

# ==============================================================================

# Example CI/CD targets are: dependencies, build, publish, deploy, clean, etc.

.PHONEY: dependencies
dependencies: # Install dependencies needed to build and test the project @Pipeline
	cd gateway-api && poetry install

.PHONEY: build-gateway-api
build-gateway-api: dependencies
	@cd gateway-api
	@echo "Running type checks..."
	@poetry run mypy src/
	@rm -rf target && rm -rf dist
	@echo "Packaging dependencies..."
	@poetry build --format=wheel
	@pip install "dist/gateway_api-0.1.0-py3-none-any.whl" --target "./target/gateway-api"
	@cp -r ./target/gateway-api ../infrastructure/images/gateway-api/resources/build/

.PHONEY: build
build: build-gateway-api # Build the project artefact @Pipeline
	@echo "Building Docker image using Docker..."
	@docker buildx build  --load -t gateway-api-image infrastructure/images/gateway-api
	@echo "Docker image 'gateway-api-image' built successfully!"

publish: # Publish the project artefact @Pipeline
	# TODO: Implement the artefact publishing step

deploy: # Deploy the project artefact to the target environment @Pipeline
	# TODO: Implement the artefact deployment step

clean:: # Clean-up project resources (main) @Operations
	# TODO: Implement project resources clean-up step

config:: # Configure development environment (main) @Configuration
	# TODO: Use only 'make' targets that are specific to this project, e.g. you may not need to install Node.js
	make _install-dependencies

.PHONEY: pre-commit
pre-commit:
	make githooks-run

# ==============================================================================

${VERBOSE}.SILENT: \
	build \
	clean \
	config \
	dependencies \
	deploy \

else

PYTHON_VERSION=3.13.9

.PHONEY: clean
clean:
	@echo "Stopping Build Container..."
	@podman stop gateway-api-build-container || echo "No build container currently running."
	@echo "Removing Build Container..."
	@podman rm gateway-api-build-container || echo "No build container image currently built."


.PHONEY: env
env: clean
	@echo "Building Build Container..."
	# Required so that asdf plugins can be installed whilst building the container.
	@cp .tool-versions ./infrastructure/images/build-container/resources/.tool-versions
	@podman build --build-arg PYTHON_VERSION=${PYTHON_VERSION} --build-arg INCLUDE_DEV_CERTS=true -t gateway-api-build-container  infrastructure/images/build-container
	@echo "Starting Build Container..."
	@podman run -v /var/run/docker.sock:/var/run/docker.sock --mount type=bind,src=$(PWD),dest=/git --security-opt label=disable -d --name=gateway-api-build-container gateway-api-build-container

	make dependencies

	@echo "Done!"

.PHONEY: dependencies
dependencies:
	@echo "Configuring Git safe directory..."
	@git config --global --add safe.directory /git || true
	@echo "Installing git hooks..."
	@cp ./scripts/githooks/pre-commit ./.git/hooks/pre-commit
	@chmod u+x ./.git/hooks/pre-commit
	@echo "Installing project dependencies within build container..."
	COMMAND="pyenv activate gateway && make dependencies" make command

.PHONEY: bash
bash:
	COMMAND=bash make command

.PHONEY: pre-commit
pre-commit:
	COMMAND="make pre-commit" make command

.PHONEY: build
build:
	COMMAND="pyenv activate gateway && make build" make command

.PHONEY: command
command:
	@podman exec -it gateway-api-build-container bash -c 'source ~/.bashrc && ${COMMAND}'

endif
