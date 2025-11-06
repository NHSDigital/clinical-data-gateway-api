# Gateway API BDD Tests

This directory contains the BDD (Behavior-Driven Development) acceptance test suite for the gateway API using behave.

## Test Structure

- `*.feature` - Gherkin feature files describing user-facing behavior
- `steps/*.py` - Step definitions that implement the Gherkin steps
- `environment.py` - Test setup/teardown hooks

## Running Tests

### Install Dependencies (if not using Dev container)

Dev container users can skip this - dependencies are pre-installed during container build.

```bash
cd gateway-api
poetry install --with dev
```

### Run All BDD Tests with Verbose Output

```bash
poetry run behave --verbose
```

### Run Specific Feature

```bash
poetry run behave features/hello_world.feature
```

### Debug Mode (Show All Output)

```bash
poetry run behave --no-capture
```

## BDD Testing with Behave

BDD tests describe system behavior from a user's perspective using natural language (Gherkin syntax). These tests spin up the Flask application and test end-to-end scenarios.

### How It Works

1. **Feature Files** (`.feature`)
   - Written in Gherkin syntax (Given/When/Then)
   - Describe behavior in plain English
   - Readable by non-technical stakeholders
   - Define acceptance criteria

2. **Step Definitions** (`steps/*.py`)
   - Python code that implements each Gherkin step
   - Uses Flask test client to interact with the API
   - Contains assertions to verify expected behavior

3. **Environment Hooks** (`environment.py`)
   - `before_all()` - Set up Flask test environment once
   - `before_scenario()` - Set up before each scenario
   - `after_scenario()` - Clean up after each scenario
   - `after_all()` - Final cleanup
