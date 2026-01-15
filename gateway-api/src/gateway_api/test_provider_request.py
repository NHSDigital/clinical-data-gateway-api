"""
Unit tests for :mod:`gateway_api.provider_request`.
"""

# imports
from typing import Any

import pytest
import requests
from requests import Response
from stubs.stub_provider import GpProviderStub

from gateway_api.provider_request import GpProviderClient

# definitions
ars_InteractionID = "urn:nhs:names:services:gpconnect:structured:fhir:operation:gpc.getstructuredrecord-1"  # noqa: E501 this is standard InteractionID for accessRecordStructured


# fixtures
@pytest.fixture
def stub() -> GpProviderStub:
    return GpProviderStub()


@pytest.fixture
def mock_request_post(
    monkeypatch: pytest.MonkeyPatch, stub: GpProviderStub
) -> dict[str, Any]:
    """
    Patch requests.post method so calls are routed here.

    The fixture returns a "capture" dict recording the most recent request header
    information. This is used by header-related tests.
    """
    capture: dict[str, Any] = {}

    def _fake_post(
        url: str,
        headers: dict[str, str],
        data: str,
        timeout: int,
    ) -> Response:
        """A fake requests.post implementation."""

        capture["headers"] = dict(headers)
        capture["data"] = data

        stub_response = stub.access_record_structured()

        return stub_response

    monkeypatch.setattr(requests, "post", _fake_post)
    return capture


# pseudo-code for tests:

# Test: (throws if not 200 OK)
# Test: ~~throws if invalid response from stub provider~~

# Test: the expected headers are returned - this would be testing the behaviour of the
# (stub) provider so not in scope here


def test_valid_gpprovider_access_structured_record_with_correct_headers_post_200(
    mock_request_post: dict[str, Any],
    stub: GpProviderStub,
) -> None:
    """
    Verify that a request to the GPProvider is made with the correct headers,
    and receives a 200 OK response.
    """
    # Arrange
    provider_asid = "200000001154"
    consumer_asid = "200000001152"
    provider_endpoint = "https://invalid.com"
    trace_id = "some_uuid_value"

    client = GpProviderClient(
        provider_endpoint=provider_endpoint,
        provider_asid=provider_asid,
        consumer_asid=consumer_asid,
    )
    expected_headers = {
        "Content-Type": "application/fhir+json",
        "Accept": "application/fhir+json",
        "Ssp-TraceID": str(trace_id),
        "Ssp-From": consumer_asid,
        "Ssp-To": provider_asid,
        "Ssp-InteractionID": ars_InteractionID,
    }
    # Act
    result = client.access_structured_record(trace_id, "body")

    # Extract
    captured_headers = mock_request_post["headers"]

    # Assert
    for key, value in expected_headers.items():
        assert captured_headers.get(key) == value
    assert result.status_code == 200


# Test: makes request with correct body
def test_valid_gpprovider_access_structured_record_with_correct_body_200(
    mock_request_post: dict[str, Any],
    stub: GpProviderStub,
) -> None:
    """
    Verify that a request to the GPProvider is made with the correct body,
    and receives a 200 OK response.
    """
    # Arrange
    provider_asid = "200000001154"
    consumer_asid = "200000001152"
    provider_endpoint = "https://invalid.com"
    trace_id = "some_uuid_value"

    request_body = "some_FHIR_request_params"

    client = GpProviderClient(
        provider_endpoint=provider_endpoint,
        provider_asid=provider_asid,
        consumer_asid=consumer_asid,
    )

    # Act
    result = client.access_structured_record(trace_id, request_body)

    # Extract
    captured_body = mock_request_post["data"]

    # Assert
    assert result.status_code == 200
    assert captured_body == request_body


# Test: returns what is received from stub provider (if valid)
def test_valid_gpprovider_access_structured_record_returns_stub_response_200(
    mock_request_post: dict[str, Any],
    stub: GpProviderStub,
) -> None:
    """
    Verify that a request to the GPProvider returns the same response
    as provided by the stub provider.
    """
    # Arrange
    provider_asid = "200000001154"
    consumer_asid = "200000001152"
    provider_endpoint = "https://invalid.com"
    trace_id = "some_uuid_value"

    client = GpProviderClient(
        provider_endpoint=provider_endpoint,
        provider_asid=provider_asid,
        consumer_asid=consumer_asid,
    )

    expected_response = stub.access_record_structured()

    # Act
    result = client.access_structured_record(trace_id, "body")

    # Assert
    assert result.status_code == expected_response.status_code
    assert result.content == expected_response.content
