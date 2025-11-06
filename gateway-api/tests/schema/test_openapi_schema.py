"""Schemathesis-based API schema validation tests.

This test suite uses property-based testing to automatically generate test cases
from the OpenAPI specification and validate the API implementation.
"""

import schemathesis

# Load the OpenAPI schema from the local file
schema = schemathesis.openapi.from_file("openapi.yaml")


@schema.parametrize()
def test_api_schema_compliance(case):
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
    # Call the API and validate the response against the schema
    case.call_and_validate()
