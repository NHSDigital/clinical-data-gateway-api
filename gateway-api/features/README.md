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

### Run All BDD Tests

```bash
poetry run behave
```

### Run with Verbose Output

```bash
poetry run behave --verbose
```

### Run Specific Feature

```bash
poetry run behave features/hello_world.feature
```

### Run with Tags

```bash
# Run only tests tagged with @smoke
poetry run behave --tags=@smoke

# Exclude tests tagged with @wip (work in progress)
poetry run behave --tags=~@wip
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

### The Flow

```text
Feature File → Behave Parser → Step Definitions → Flask Test Client → Assertions
     ↓
Gherkin Steps                      Python Code         HTTP Calls      Pass/Fail
```

### Why BDD Tests?

- **Executable specifications** - Tests are documentation
- **Stakeholder collaboration** - Business people can read/write scenarios
- **Living documentation** - Tests describe what the system actually does
- **End-to-end validation** - Tests real user workflows
- **Complement unit tests** - Focus on behavior, not implementation

## Writing New Tests

### 1. Create a Feature File

```gherkin
Feature: User Login
  As a user
  I want to log in to the system
  So that I can access protected resources

  Background:
    Given the API is running

  Scenario: Successful login
    When I send a POST request to "/login" with valid credentials
    Then the response status code should be 200
    And the response should contain an access token
```

### 2. Implement Step Definitions

```python
@when('I send a POST request to "{endpoint}" with valid credentials')
def step_login_with_valid_credentials(context, endpoint):
    context.response = context.client.post(endpoint, json={
        "username": "testuser",
        "password": "password123"
    })

@then("the response should contain an access token")
def step_check_access_token(context):
    data = context.response.get_json()
    assert "access_token" in data
```

### 3. Run and Verify

```bash
poetry run behave features/login.feature
```

## Gherkin Best Practices

- **Keep scenarios focused** - One scenario per behavior
- **Use Background for common setup** - Avoid repetition
- **Make scenarios readable** - Anyone should understand them
- **Avoid technical details** - Focus on business behavior
- **Use Scenario Outlines** - For testing multiple inputs

### Example Scenario Outline

```gherkin
Scenario Outline: HTTP status codes
  When I send a GET request to "<endpoint>"
  Then the response status code should be <status>

  Examples:
    | endpoint       | status |
    | /              | 200    |
    | /nonexistent   | 404    |
    | /health        | 200    |
```

## Comparison with Other Tests

| Test Type | Purpose | Speed | When to Run |
|-----------|---------|-------|-------------|
| Unit Tests (pytest) | Test individual functions/classes | Fast | On every change |
| Contract Tests (Pact) | Test API contract agreement | Medium | Before integration |
| BDD Tests (behave) | Test user-facing behavior | Slower | Before deployment |

**BDD tests** complement unit and contract tests by focusing on complete user workflows rather than individual components or contracts.
