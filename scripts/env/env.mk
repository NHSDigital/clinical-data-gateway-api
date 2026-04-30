.PHONY: env env-% _env

env: # Create .env file with environment variables for development environment (stubs)
	make _env env="dev"

env-dev: # Create .env file with environment variables for development environment (stubs)
	make _env env="dev"

env-ci: # Create .env file with environment variables for CI environment (stubs)
	make _env env="ci"

env-orangebox: # Create .env file that will have the app send requests to the provider "orangebox", stubs otherwise.
	make _env env="orangebox"

env-sandbox: # Create .env file that will have the app send requests to the SDS and PDS sandbox environment, stubs otherwise.
	make _env env="sandbox"

env-int: # Create .env file that will have the app send requests to the SDS and PDS integration environments.
	make _env env="int"

env-test-local: # Create .env.test file that will have tests send requests to the local app.
	make _env-test env="local"
	make env-dev # Ensure unit tests run with stub environment variables

env-test-ci: # Create .env.test file that will have tests send requests to a CI-local app.
	make _env-test env="ci"
	make env-ci # Ensure unit tests run with stub environment variables

env-test-pr-%: # Create .env.test file that will have tests send requests to a proxy deployed for the PR.
	make _env-test env="pr-$*"

env-test-alpha-int: # Create .env.test file that will have tests send requests to the alpha integration environment.
	make _env-test env="alpha-int"

_env:
	scripts/env/app/env.sh "$(env)"

_env-test:
	scripts/env/test/env.sh "$(env)"

${VERBOSE}.SILENT: \
	_env \
	env \
	env-dev \
	env-ci \
	env-orangebox \
	env-sandbox \
	env-int \
	env-int-pds \
	env-int-sds \
	_env-test \
	env-test-local \
	env-test-ci \
	env-test-pr-%
