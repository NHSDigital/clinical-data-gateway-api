"""
Unit tests for :mod:`gateway_api.provider_request`.
"""

# makes valid requests to stub provider and checks responses


# (throws if not 200 OK)

# returns what is received from stub provider (if valid)

# ~~throws if invalid response from stub provider~~

from gateway_api.provider_request import GPProviderClient


# receives 200 OK from example.com for valid request
def test_valid_gpprovider_request_get_200() -> None:
    """
    Verify that a valid request to the GPProvider returns a 200 OK response.
    """
    # Arrange
    provider_asid = "200000001154"
    consumer_asid = "200000001152"
    provider_endpoint = "http://example.com"  # this will be monkeypatched in real tests

    client = GPProviderClient(
        provider_endpoint=provider_endpoint,
        provider_asid=provider_asid,
        consumer_asid=consumer_asid,
    )

    # Act
    result = client.get_structured_record()

    # Assert
    assert result.status_code == 200
