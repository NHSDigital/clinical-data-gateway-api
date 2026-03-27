# The test types listed here are both those which might run both locally and in CI, or
# in one but not the other.  All of the test types listed at
# https://github.com/NHSDigital/software-engineering-quality-framework/blob/main/quality-checks.md
# should be represented here with the exception of:
#   - dependency scanning, which we expect to be applied at the repository level
#   - secret scanning, which we expect to be a pre-commit hook
#   - code review, which is outside the scope of automated testing for the moment

test-unit: # Run your unit tests from scripts/test/unit @Testing
	make _test name="unit"

test-lint: # Lint your code from scripts/test/lint @Testing
	make _test name="lint"

test-coverage: # Evaluate code coverage from scripts/test/coverage @Testing
	make _test name="coverage"

test-accessibility: # Run your accessibility tests from scripts/test/accessibility @Testing
	make _test name="accessibility"

test-contract: # Run your contract tests from scripts/test/contract @Testing
	make _test name="contract"

test-schema: # Run your schema tests from scripts/test/schema @Testing
	make _test name="schema"

test-integration: # Run your integration tests from scripts/test/integration @Testing
	make _test name="integration"

test-acceptance: # Run your acceptance tests from scripts/test/acceptance @Testing
	make _test name="acceptance"

test-load: # Run all your load tests @Testing
	make \
		test-capacity \
		test-soak \
		test-response-time
		# You may wish to add more here, depending on your app

test-capacity: # Test what load level your app fails at from scripts/test/capacity @Testing
	make _test name="capacity"

test-soak: # Test that resources don't get exhausted over time from scripts/test/soak @Testing
	make _test name="soak"

test-response-time: # Test your API response times from scripts/test/response-time @Testing
	make _test name="response-time"

test-security: # Run your security tests from scripts/test/security @Testing
	make _test name="security"

test-ui: # Run your UI tests from scripts/test/ui @Testing
	make _test name="ui"

test-ui-performance: # Run UI render tests from scripts/test/ui-performance @Testing
	make _test name="ui-performance"

test: # Run all the test tasks @Testing
	make \
		test-unit \
		test-lint \
		test-contract \
		test-security \
		test-ui \
		test-ui-performance \
		test-integration \
		test-accessibility \
		test-load \
		test-acceptance\
		test-schema

_test:
	set -e
	script="./scripts/tests/${name}.sh"
	if [ -e "$${script}" ]; then
		exec $${script}
	else
		echo "make test-${name} not implemented: $${script} not found" >&2
	fi

${VERBOSE}.SILENT: \
	_test \
	test \
	test-accessibility \
	test-capacity \
	test-contract \
	test-coverage \
	test-soak \
	test-integration \
	test-lint \
	test-load \
	test-response-time \
	test-security \
	test-ui \
	test-ui-performance \
	test-unit \
	test-acceptance \
	test-schema\

# ---------------------------------------------------------------------------
# Local vs remote environment helpers
# ---------------------------------------------------------------------------
# Usage:
#   make test-local		-	activate .env.local, run tests against local
#												and api-gateway-mock
#   make test-remote	- activate .env.remote, obtain an APIGEE token, run
#                       tests against APIM proxy
#
# 	.env.local     		- local env config (ENV=local, BASE_URL,HOST)
# 	.env.remote     	- remote env config (ENV=remote, BASE_URL,HOST,PR_NUMBER,PROXYGEN_API_NAME)
# 	.env           		- active env, overwritten by env-local/env-remote
#
# The .env file is deterministically overwritten each time you switch
# environments so the test runner always sees a consistent configuration.
# ===========================================================================

.PHONY: env-local env-remote test-local test-remote

env-local:
		@if [ ! -f .env.local ]; then \
				echo "ERROR: .env.local not found. Needs creating." >&2; \
				exit 1; \
		fi
		cp -f .env.local .env
		@echo "Activated local environment: .env.local -> .env (ENV=local)"

env-remote:
		@if [ ! -f .env.remote ]; then \
				echo "ERROR: .env.remote not found. Needs creating." >&2; \
				exit 1; \
		fi
		cp -f .env.remote .env
		@echo "Activated remote environment: .env.remote -> .env (ENV=remote)"

# Run tests against local
test-local: env-local
	@echo "Obtaining APIGEE access token..."
	@set -a && source .env && set +a && \
		APIGEE_ACCESS_TOKEN="$$(./scripts/get_apigee_token.sh)" && \
		export APIGEE_ACCESS_TOKEN && \
		$(MAKE) test

# Run tests against remote, exporting APIGEE_ACCESS_TOKEN only
test-remote: env-remote
	@echo "Obtaining APIGEE access token..."
	@set -a && source .env && set +a && \
		APIGEE_ACCESS_TOKEN="$$(./scripts/get_apigee_token.sh)" && \
		BASE_URL="$${BASE_URL}-pr-$${PR_NUMBER}" && \
		export APIGEE_ACCESS_TOKEN BASE_URL && \
		$(MAKE) test
