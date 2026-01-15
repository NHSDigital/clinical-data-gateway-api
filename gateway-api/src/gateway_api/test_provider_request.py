"""
Unit tests for :mod:`gateway_api.provider_request`.
"""

# imports
import pytest
import requests
from requests import Response
from stubs.stub_provider import GPProviderStub

from gateway_api.provider_request import GPProviderClient

# definitions


# fixtures
@pytest.fixture
def stub() -> GPProviderStub:
    return GPProviderStub()


@pytest.fixture
def mock_request_post(monkeypatch: pytest.MonkeyPatch, stub: GPProviderStub) -> None:
    """
    Patch requests.post method so calls are routed here.
    """

    def _fake_post(
        url: str,
        headers: dict[str, str],  # TODO: define a class 'GPConnectHeaders' for this
        timeout: int,
    ) -> Response:
        """A fake requests.post implementation."""

        stub_response = stub.access_record_structured()

        return stub_response

    monkeypatch.setattr(requests, "post", _fake_post)


# pseudo-code for tests:
# makes valid requests to stub provider and checks responses using a capture

# returns what is received from stub provider (if valid)

# (throws if not 200 OK)
# ~~throws if invalid response from stub provider~~


# receives 200 OK from example.com for valid request
def test_valid_gpprovider_access_structured_record_post_200(
    mock_request_post: Response,
    stub: GPProviderStub,
) -> None:
    """
    Verify that a valid request to the GPProvider returns a 200 OK response.
    """
    # Arrange
    provider_asid = "200000001154"
    consumer_asid = "200000001152"
    provider_endpoint = "http://invalid.com"

    client = GPProviderClient(
        provider_endpoint=provider_endpoint,
        provider_asid=provider_asid,
        consumer_asid=consumer_asid,
    )

    # Act
    result = client.access_structured_record()

    # Assert
    assert result.status_code == 200
