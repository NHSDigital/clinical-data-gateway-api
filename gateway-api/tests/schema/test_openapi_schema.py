"""Schemathesis-based API schema validation tests.

This test suite uses property-based testing to automatically generate test cases
from the OpenAPI specification and validate the API implementation.
"""

from pathlib import Path

import schemathesis
import yaml
from hypothesis import HealthCheck, settings
from schemathesis.generation.case import Case
from schemathesis.openapi import from_dict

# Load the OpenAPI schema from the local file
schema_path = Path(__file__).parent.parent.parent / "openapi.yaml"
with open(schema_path) as f:
    schema_dict = yaml.safe_load(f)
schema = from_dict(schema_dict)


# Schemathesis warns you that this test is running a function-scoped fixture - a fixture
# that is executed once per test function, not per test case. Given schemathesis
# generates multiple test cases from the same test function, this means that the fixture
# will be executed only once for all generated cases, this can be a problem for certain
# fixtures. However, in this case, as base_url should not change during a test run,
# using the cached value for each test case is acceptable.
# See https://hypothesis.readthedocs.io/en/latest/reference/api.html#hypothesis.HealthCheck.function_scoped_fixture
@schema.parametrize()
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_api_schema_compliance(case: Case, base_url: str) -> None:
    """Test API endpoints against the OpenAPI schema.

    Schemathesis automatically generates test cases with:
    - Valid inputs
    - Edge cases
    - Invalid inputs
    - Boundary values

    This test verifies that the API:
    - Returns responses matching the schema
    - Handles edge cases correctly
    - Validates inputs properly
    - Returns appropriate status codes
    """

    case.headers["Ods-from"] = "test-ods-code"
    case.headers["Ssp-TraceID"] = "test-trace-id"

    case.call_and_validate(
        base_url=base_url,
        excluded_checks=[
            # GPCAPIM-421
            schemathesis.checks.not_a_server_error,
            # GPCAPIM-419
            schemathesis.checks.missing_required_header,
            # GPCAPIM-422
            schemathesis.checks.unsupported_method,
        ],
        timeout=30,
    )
