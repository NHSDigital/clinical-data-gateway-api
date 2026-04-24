# NHSE Clinical Data Gateway API

Our core programming language is Python.

Our docs are in README.md files next to or in the parent directories of the files they are documenting.

This repository is for handling HTTP requests from "Consumer systems" and forwarding them on to "Provider systems", while performing a number of checks on and additions to the request. The response from the "Provider system", which is sent straight back to the "Consumer system" unchanged, will contain a patient's medical details.

We use other NHSE services to assist in the validation and processing of the requests including PDS FHIR API for obtaining GP practice codes for the patient, SDS FHIR API for obtaining the "Provider system" details of that GP practice and Healthcare Worker FHIR API for obtaining details of the requesting practitioner using the "Consumer System" that will then be added to the forwarded request.

`make deploy` will build and start a container running Gateway API at `localhost:5000`.

After deploying the container locally, `make test` will run all tests and capture their coverage. Note: env variables control the use of stubs for the PDS FHIR API, SDS FHIR API, Healthcare Worker FHIR API and Provider system services.

Individual test suites can be run with:

- Unit tests: `make test-unit`
- Acceptance tests: `make test-acceptance`
- Integration tests: `make test-integration`
- Schema tests: `make test-schema`
- Contract tests: `make test-contract`

The container must be running in order to successfully run any of the test suites other than the unit tests.

The schema for this API can be found in `gateway-api/openapi.yaml`.

## Code reviews

When reviewing code, ensure you compare the changes made to files to all README.md containing directory structures, and update the directory structures accordingly.

## Docstrings and comments

- Use precise variable and function names to reduce the need for comments
- Use docstrings on high-level functions and classes to explain their purpose, inputs, outputs, and any side effects
- Avoid comments that state the obvious or repeat what the code does; instead, focus on explaining the intent behind the code, the reasons for non-obvious decisions, and any important trade-offs or constraints

## Formatting

- For Python files, use 4-space indentation and keep line lengths within Ruff limits (default 88 chars unless configured otherwise)
- For Python changes, keep code compatible with both `ruff format` and `ruff check`
- Let Ruff manage import ordering (isort rules are enabled via Ruff)
- Follow `.editorconfig` basics for all files: UTF-8, LF line endings, final newline, and no trailing whitespace
- Use tabs (not spaces) in `Makefile` and `.mk` files, per `.editorconfig`
- When wrapping a long string value inside parentheses, do not add a trailing comma if the value must remain a string
- For Markdown changes, keep content compatible with markdownlint checks (rules in `scripts/config/.markdownlint.yaml`; enforced by `scripts/githooks/check-markdown-format.sh`)
- For Markdown prose, write content that passes Vale English usage checks (rules in `scripts/config/vale/vale.ini`; enforced by `scripts/githooks/check-english-usage.sh`)
- For Terraform changes, keep files compatible with `terraform fmt`

## Commits

Prepend `[AI-generated]` to the commit message when committing changes made by an AI agent.

## Branches

When creating a branch for a Jira ticket, use:

`feature/<JIRA_TICKET>_<Short_description>`

Example: `feature/GPCAPIM-395_Local_PDS_INT_Integration`

## Security

This repository is public. Do not commit any secrets, tokens or credentials.
