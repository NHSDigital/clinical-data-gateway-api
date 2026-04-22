.PHONY: env env-% _env

env env-dev env-ci: # Create .env file with environment variables for development environment (stubs)
	make _env env="dev"

env-orangebox: # Create .env file that will have the app send requests to the provider "orangebox", stubs otherwise.
	make _env env="orangebox"

env-sandbox-pds: # Create .env file that will have the app send requests to the PDS sandbox environment (sandbox PDS), stubs otherwise.
	make _env env="sandbox-pds"

env-sandbox-sds: # Create .env file that will have the app send requests to the SDS sandbox environment (sandbox SDS), stubs otherwise.
	make _env env="sandbox-sds"

env-int: # Create .env file with environment variables for integration environment
	make _env env="int"

env-test-local: # Create .env.test file that will have tests send requests to the local app.
	make _env-test env="local"
	make env-dev # Ensure unit tests run with stub environment variables

env-test-ci: # Create .env.test file that will have tests send requests to a CI-local app.
	make _env-test env="ci" overwrite=true
	make env-ci # Ensure unit tests run with stub environment variables

env-test-pr-%: # Create .env.test file that will have tests send requests to a proxy deployed for the PR.
	make _env-test env="pr-$*" overwrite=true

env-test-alpha-int: # Create .env.test file that will have tests send requests to the alpha integration environment.
	make _env-test env="alpha-int" overwrite=true

_env:
	scripts/env/app-env.sh "$(env)"

_env-test:
	scripts/env/test-env.sh "$(env)" "$(overwrite)"

${VERBOSE}.SILENT: \
	_env \
	env \
	env-dev \
	env-orangebox \
	env-sandbox-pds \
	env-sandbox-sds \
	env-int \
	env-test-local \
	env-test-ci \
	env-test-pr-%
