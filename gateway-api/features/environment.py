"""Behave environment setup for Flask application testing.

This file contains hooks that run before and after test scenarios.
"""

from gateway_api.main import app


def before_all(context):
    """Set up test environment before running any features.

    Args:
        context: Behave context object available to all tests
    """
    # Configure Flask for testing
    app.config.update(
        {
            "TESTING": True,
        }
    )

    # Create test client
    context.client = app.test_client()
    context.app = app


def before_scenario(context, scenario):
    """Set up before each scenario.

    Args:
        context: Behave context object
        scenario: The scenario about to run
    """
    # Reset any state if needed
    pass


def after_scenario(context, scenario):
    """Clean up after each scenario.

    Args:
        context: Behave context object
        scenario: The scenario that just ran
    """
    # Clean up resources if needed
    pass


def after_all(context):
    """Clean up after all features have run.

    Args:
        context: Behave context object
    """
    # Final cleanup if needed
    pass
