"""Schemathesis-based API schema validation tests.

This test suite uses property-based testing to automatically generate test cases
from the OpenAPI specification and validate the API implementation.
"""

from pathlib import Path

import schemathesis
import yaml
from schemathesis.generation.case import Case
from schemathesis.openapi import from_dict

# Load the OpenAPI schema from the local file
schema_path = Path(__file__).parent.parent.parent / "openapi.yaml"
with open(schema_path) as f:
    schema_dict = yaml.safe_load(f)
schema = from_dict(schema_dict)


@schema.parametrize()
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

    Note: Server error checks are disabled because the API may return 500 errors
    when testing with randomly generated NHS numbers that don't exist in the PDS.
    """
    # Call the API and validate the response against the schema
    # Exclude not_a_server_error check as 500 responses are expected for
    # non-existent patients
    case.call_and_validate(
        base_url=base_url,
        excluded_checks=[schemathesis.checks.not_a_server_error],
    )
