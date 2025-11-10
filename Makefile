# This file is for you! Edit it to implement your own hooks (make targets) into
# the project as automated steps to be executed on locally and in the CD pipeline.

ifeq (${IN_BUILD_CONTAINER},true)
include scripts/init.mk

# ==============================================================================

# Example CI/CD targets are: dependencies, build, publish, deploy, clean, etc.

dependencies: # Install dependencies needed to build and test the project @Pipeline
	@if [[ -n "$${DEV_CERT_PATH}" ]]; then \
		echo "Configuring poetry to trust the dev certificate..."  ; \
		poetry config certificates.PyPI.cert $${DEV_CERT_PATH} ; \
	fi
	cd gateway-api && poetry install --extras dev

build: # Build the project artefact @Pipeline
	# TODO: Implement the artefact build step

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

# ==============================================================================

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
	@if [[ -z "$${DEV_CERT_FILENAME:-}" ]]; then \
		podman build --build-arg PYTHON_VERSION=${PYTHON_VERSION} --build-arg INCLUDE_DEV_CERTS=true -t gateway-api-build-container infrastructure/images/build-container; \
	else \
		echo "including development certificate: ${DEV_CERT_FILENAME}"; \
		podman build --build-arg PYTHON_VERSION=${PYTHON_VERSION} --build-arg INCLUDE_DEV_CERTS=true --build-arg DEV_CERT_FILENAME=${DEV_CERT_FILENAME} -t gateway-api-build-container infrastructure/images/build-container; \
	fi
	@echo "Starting Build Container..."
	@podman run -v /var/run/docker.sock:/var/run/docker.sock --mount type=bind,src=$(PWD),dest=/git --security-opt label=disable -d --name=gateway-api-build-container gateway-api-build-container

	make dependencies

	@echo "Done!"

.PHONEY: dependencies
dependencies:
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

.PHONEY: command
command:
	@podman exec -it gateway-api-build-container bash -c 'source ~/.bashrc && ${COMMAND}'

endif
