"""
Unit tests for :mod:`gateway_api.provider_request`.

This module contains unit tests for the `GpProviderClient` class, which is responsible
for interacting with the GPProvider FHIR API.

"""

from typing import Any

import pytest
from requests import Response
from requests.structures import CaseInsensitiveDict
from stubs.stub_provider import GpProviderStub

from gateway_api import provider_request
from gateway_api.provider_request import ExternalServiceError, GpProviderClient

ars_interactionId = (
    "urn:nhs:names:services:gpconnect:structured"
    ":fhir:operation:gpc.getstructuredrecord-1"
)


@pytest.fixture
def stub() -> GpProviderStub:
    return GpProviderStub()


@pytest.fixture
def mock_request_post(
    monkeypatch: pytest.MonkeyPatch, stub: GpProviderStub
) -> dict[str, Any]:
    """
    Fixture to patch the `requests.post` method for testing.

    This fixture intercepts calls to `requests.post` and routes them to the
    stub provider. It also captures the most recent request details, such as
    headers, body, and URL, for verification in tests.

    Returns:
        dict[str, Any]: A dictionary containing the captured request details.
    """
    capture: dict[str, Any] = {}

    def _fake_post(
        url: str,
        headers: CaseInsensitiveDict[str],
        data: str,
        timeout: int,  # NOQA ARG001 (unused in stub)
    ) -> Response:
        """A fake requests.post implementation."""

        capture["headers"] = dict(headers)
        capture["data"] = data
        capture["url"] = url

        # Provide dummy or captured arguments as required by the stub signature
        return stub.access_record_structured(
            trace_id=headers.get("Ssp-TraceID", "dummy-trace-id"), body=data
        )

    monkeypatch.setattr(provider_request, "post", _fake_post)
    return capture


def test_valid_gpprovider_access_structured_record_makes_request_correct_url_post_200(
    mock_request_post: dict[str, Any],
) -> None:
    """
    Test that the `access_structured_record` method constructs the correct URL
    for the GPProvider FHIR API request and receives a 200 OK response.

    This test verifies that the URL includes the correct FHIR base path and
    operation for accessing a structured patient record.
    """
    provider_asid = "200000001154"
    consumer_asid = "200000001152"
    provider_endpoint = "https://test.com"
    trace_id = "some_uuid_value"

    client = GpProviderClient(
        provider_endpoint=provider_endpoint,
        provider_asid=provider_asid,
        consumer_asid=consumer_asid,
    )

    result = client.access_structured_record(trace_id, "body")

    captured_url = mock_request_post.get("url", provider_endpoint)

    assert (
        captured_url
        == provider_endpoint + "/FHIR/STU3/patient/$gpc.getstructuredrecord"
    )
    assert result.status_code == 200


def test_valid_gpprovider_access_structured_record_with_correct_headers_post_200(
    mock_request_post: dict[str, Any],
) -> None:
    """
    Test that the `access_structured_record` method includes the correct headers
    in the GPProvider FHIR API request and receives a 200 OK response.

    This test verifies that the headers include:
        - Content-Type and Accept headers for FHIR+JSON.
        - Ssp-TraceID, Ssp-From, Ssp-To, and Ssp-InteractionID for GPConnect.
    """
    provider_asid = "200000001154"
    consumer_asid = "200000001152"
    provider_endpoint = "https://test.com"
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
        "Ssp-InteractionID": ars_interactionId,
    }

    result = client.access_structured_record(trace_id, "body")

    captured_headers = mock_request_post["headers"]

    assert expected_headers == captured_headers
    assert result.status_code == 200


def test_valid_gpprovider_access_structured_record_with_correct_body_200(
    mock_request_post: dict[str, Any],
) -> None:
    """
    Test that the `access_structured_record` method includes the correct body
    in the GPProvider FHIR API request and receives a 200 OK response.

    This test verifies that the request body matches the expected FHIR parameters
    resource sent to the GPProvider API.
    """
    provider_asid = "200000001154"
    consumer_asid = "200000001152"
    provider_endpoint = "https://test.com"
    trace_id = "some_uuid_value"

    request_body = "some_FHIR_request_params"

    client = GpProviderClient(
        provider_endpoint=provider_endpoint,
        provider_asid=provider_asid,
        consumer_asid=consumer_asid,
    )

    result = client.access_structured_record(trace_id, request_body)

    captured_body = mock_request_post["data"]

    assert result.status_code == 200
    assert captured_body == request_body


def test_valid_gpprovider_access_structured_record_returns_stub_response_200(
    mock_request_post: dict[str, Any],  # NOQA ARG001 (Mock not called directly)
    stub: GpProviderStub,
) -> None:
    """
    Test that the `access_structured_record` method returns the same response
    as provided by the stub provider.

    This test verifies that the response from the GPProvider FHIR API matches
    the expected response, including the status code and content.
    """
    provider_asid = "200000001154"
    consumer_asid = "200000001152"
    provider_endpoint = "https://test.com"
    trace_id = "some_uuid_value"

    client = GpProviderClient(
        provider_endpoint=provider_endpoint,
        provider_asid=provider_asid,
        consumer_asid=consumer_asid,
    )

    expected_response = stub.access_record_structured(trace_id, "body")

    result = client.access_structured_record(trace_id, "body")

    assert result.status_code == 200
    assert result.content == expected_response.content


def test_access_structured_record_raises_external_service_error(
    mock_request_post: dict[str, Any],  # NOQA ARG001 (Mock not called directly)
) -> None:
    """
    Test that the `access_structured_record` method raises an `ExternalServiceError`
    when the GPProvider FHIR API request fails with an HTTP error.
    """
    provider_asid = "200000001154"
    consumer_asid = "200000001152"
    provider_endpoint = "https://test.com"
    trace_id = "invalid for test"

    client = GpProviderClient(
        provider_endpoint=provider_endpoint,
        provider_asid=provider_asid,
        consumer_asid=consumer_asid,
    )

    with pytest.raises(
        ExternalServiceError,
        match="GPProvider FHIR API request failed:Bad Request",
    ):
        client.access_structured_record(trace_id, "body")
