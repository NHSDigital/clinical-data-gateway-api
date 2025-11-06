# Gateway API

## Testing

The Gateway API has three types of tests, each serving a different purpose:

- **[Unit & Contract Tests](tests/README.md)** - Developer-focused technical tests using pytest
- **[BDD Acceptance Tests](features/README.md)** - Business-focused assurance tests using behave

### Quick Test Commands

```bash
# Run all unit and contract tests
poetry run pytest -v

# Run all BDD acceptance tests
poetry run behave

# Run specific test suites
poetry run pytest tests/unit/            # Unit tests only
poetry run pytest tests/contract/        # Contract tests only
poetry run behave features/hello_world.feature  # Specific feature
```

For detailed testing documentation, see the README files in each test directory.

## Project Structure

```text
gateway-api/
├── src/
│   └── gateway_api/
│       └── main.py               # Flask application
├── tests/                         # Unit and contract tests (pytest)
│   ├── conftest.py               # Shared pytest fixtures
│   ├── unit/                     # Unit tests
│   │   └── test_main.py
│   └── contract/                 # Contract tests (Pact)
│       ├── conftest_pact.py
│       ├── test_consumer_contract.py
│       ├── test_provider_contract.py
│       └── pacts/
├── features/                      # BDD acceptance/assurance tests (behave)
│   ├── environment.py            # Behave setup
│   ├── steps/                    # Step definitions
│   └── *.feature                 # Feature files
├── pyproject.toml                # Dependencies and config
└── README.md
```
