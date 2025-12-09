# Gateway API

## Testing

The Gateway API has four types of tests, each serving a different purpose:

- **[Unit, Contract, & Schema Tests](tests/README.md)** - Developer-focused technical tests using pytest
- **[BDD Acceptance Tests](features/README.md)** - Business-focused assurance tests using behave

### Continuous Integration

All four test types (unit, contract, schema, and integration) run automatically in the CI/CD pipeline on every push and pull request. **Any test failure at any level will cause the pipeline to fail and prevent the PR from being merged.**

Additionally, code coverage is collected from all test types, merged, and analyzed by SonarCloud. PRs must meet minimum coverage thresholds to pass quality gates.

### Quick Test Commands

```bash
# Run all unit, contract, and schema tests
poetry run pytest -v

# Run all BDD acceptance tests
poetry run behave

# Run specific test suites
poetry run pytest tests/unit/            # Unit tests only
poetry run pytest tests/contract/        # Contract tests only
poetry run pytest tests/schema/          # Schema validation tests only
poetry run behave features/hello_world.feature  # Specific feature
```

For detailed testing documentation, see the README files in each test directory.

## Project Structure

```text
gateway-api/
├── src/
│   └── gateway_api/
│       └── main.py               # Flask application
├── tests/                         # Unit, contract, and schema tests (pytest)
│   ├── conftest.py               # Shared pytest fixtures
│   ├── unit/                     # Unit tests
│   │   └── test_main.py
│   ├── contract/                 # Contract tests (Pact)
│   │   ├── test_consumer_contract.py
│   │   ├── test_provider_contract.py
│   │   └── pacts/
│   └── schema/                   # Schema validation tests (Schemathesis)
│       └── test_openapi_schema.py
├── features/                      # BDD acceptance/assurance tests (behave)
│   ├── environment.py            # Behave setup
│   ├── steps/                    # Step definitions
│   └── *.feature                 # Feature files
├── openapi.yaml                  # OpenAPI 3.0 specification
├── pyproject.toml                # Dependencies and config
└── README.md
```

## External Dependencies

This module depends on the [clinical-data-common](https://github.com/NHSDigital/clinical-data-common) library for shared utilities and code. The dependency is specified as a git dependency in `pyproject.toml`:

```toml
[tool.poetry.dependencies]
clinical-data-common = { git = "https://github.com/NHSDigital/clinical-data-common.git", branch = "main" }
```

### Updating the Dependency

To pull the latest version of the common library:

```bash
poetry update clinical-data-common
```

The CI/CD pipeline automatically updates this dependency on each run to ensure the latest code from the specified branch is used during active development.
