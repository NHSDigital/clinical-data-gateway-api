"""Integration tests for the gateway API using pytest."""

import json
from collections.abc import Callable
from typing import Any

import pytest
from requests import Response
from stubs.data.bundles import Bundles

from tests.conftest import Client


class TestGetStructuredRecord:
    def test_happy_path_returns_200(
        self,
        client: Client,
        simple_request_payload: dict[str, Any],
    ) -> None:
        response = client.send_to_get_structured_record_endpoint(
            json.dumps(simple_request_payload)
        )
        assert response.status_code == 200

    def test_happy_path_returns_correct_message(
        self,
        client: Client,
        simple_request_payload: dict[str, Any],
    ) -> None:
        response = client.send_to_get_structured_record_endpoint(
            json.dumps(simple_request_payload)
        )
        assert response.json() == Bundles.ALICE_JONES_9999999999

    def test_happy_path_content_type(
        self,
        client: Client,
        simple_request_payload: dict[str, Any],
    ) -> None:
        response = client.send_to_get_structured_record_endpoint(
            json.dumps(simple_request_payload)
        )
        assert "application/fhir+json" in response.headers["Content-Type"]

    def test_happy_path_response_mirrors_request_headers(
        self,
        client: Client,
        simple_request_payload: dict[str, Any],
    ) -> None:
        headers_to_be_mirrored = {"Ssp-TraceID": "a_trace_id"}
        response = client.send_to_get_structured_record_endpoint(
            json.dumps(simple_request_payload), headers=headers_to_be_mirrored
        )
        for header_key, header_value in headers_to_be_mirrored.items():
            assert response.headers.get(header_key) == header_value

    def test_empty_request_body_returns_400_status_code(
        self, response_from_sending_request_with_empty_body: Response
    ) -> None:
        assert response_from_sending_request_with_empty_body.status_code == 400

    def test_empty_request_body_returns_invalid_request_json_message(
        self, response_from_sending_request_with_empty_body: Response
    ) -> None:
        expected = {
            "resourceType": "OperationOutcome",
            "issue": [
                {
                    "severity": "error",
                    "code": "invalid",
                    "diagnostics": "Invalid JSON body sent in request",
                }
            ],
        }
        assert response_from_sending_request_with_empty_body.json() == expected

    def test_patient_without_gp_returns_404_status_code(
        self, response_from_requesting_patient_without_gp: Response
    ) -> None:
        assert response_from_requesting_patient_without_gp.status_code == 404

    def test_patient_without_gp_returns_no_current_provider_message(
        self, response_from_requesting_patient_without_gp: Response
    ) -> None:
        expected = {
            "resourceType": "OperationOutcome",
            "issue": [
                {
                    "severity": "error",
                    "code": "exception",
                    "diagnostics": (
                        "PDS patient 9000000009 did not contain a "
                        "current provider ODS code"
                    ),
                }
            ],
        }
        assert response_from_requesting_patient_without_gp.json() == expected

    def test_no_provider_from_sds_returns_404_status_code(
        self, response_when_sds_returns_no_provider: Response
    ) -> None:
        assert response_when_sds_returns_no_provider.status_code == 404

    def test_no_provider_from_sds_returns_no_organisation_found_error(
        self, response_when_sds_returns_no_provider: Response
    ) -> None:
        expected = {
            "resourceType": "OperationOutcome",
            "issue": [
                {
                    "severity": "error",
                    "code": "exception",
                    "diagnostics": (
                        "No SDS org found for provider ODS code DoesNotExistInSDS"
                    ),
                }
            ],
        }
        assert response_when_sds_returns_no_provider.json() == expected

    def test_blank_provider_asid_from_sds_returns_404_status_code(
        self, response_when_sds_returns_blank_provider_asid: Response
    ) -> None:
        assert response_when_sds_returns_blank_provider_asid.status_code == 404

    def test_blank_provider_asid_from_sds_returns_no_asid_found_error(
        self, response_when_sds_returns_blank_provider_asid: Response
    ) -> None:
        expected = {
            "resourceType": "OperationOutcome",
            "issue": [
                {
                    "severity": "error",
                    "code": "exception",
                    "diagnostics": (
                        "SDS result for provider ODS code BlankAsidInSDS "
                        "did not contain a current ASID"
                    ),
                }
            ],
        }
        assert response_when_sds_returns_blank_provider_asid.json() == expected

    def test_502_status_code_return_when_provider_returns_error(
        self, response_when_provider_returns_error: Response
    ) -> None:
        assert response_when_provider_returns_error.status_code == 502

    def test_internal_server_error_message_returned_when_provider_returns_error(
        self, response_when_provider_returns_error: Response
    ) -> None:
        expected = {
            "resourceType": "OperationOutcome",
            "issue": [
                {
                    "severity": "error",
                    "code": "exception",
                    "diagnostics": "Provider request failed: Not Found",
                }
            ],
        }
        assert response_when_provider_returns_error.json() == expected

    def test_nhs_number_that_does_not_exist_returns_502_status_code(
        self, response_when_nhs_number_does_not_exist: Response
    ) -> None:
        assert response_when_nhs_number_does_not_exist.status_code == 502

    def test_nhs_number_that_does_not_exist_returns_no_patient_found_error(
        self, response_when_nhs_number_does_not_exist: Response
    ) -> None:
        expected = {
            "resourceType": "OperationOutcome",
            "issue": [
                {
                    "severity": "error",
                    "code": "exception",
                    "diagnostics": "PDS FHIR API request failed: Not Found",
                }
            ],
        }
        assert response_when_nhs_number_does_not_exist.json() == expected

    def test_sds_endpoint_blank_returns_404_status_code(
        self, response_when_sds_provider_endpoint_blank: Response
    ) -> None:
        assert response_when_sds_provider_endpoint_blank.status_code == 404

    def test_sds_endpoint_blank_returns_no_current_endpoint_error(
        self, response_when_sds_provider_endpoint_blank: Response
    ) -> None:
        expected = {
            "resourceType": "OperationOutcome",
            "issue": [
                {
                    "severity": "error",
                    "code": "exception",
                    "diagnostics": (
                        "SDS result for provider ODS code BlankEndpointInSDS "
                        "did not contain a current endpoint"
                    ),
                }
            ],
        }
        assert response_when_sds_provider_endpoint_blank.json() == expected

    def test_consumer_is_none_from_sds_returns_404_status_code(
        self, response_when_consumer_is_none_from_sds: Response
    ) -> None:
        assert response_when_consumer_is_none_from_sds.status_code == 404

    def test_consumer_is_none_from_sds_returns_no_organisation_found_error(
        self, response_when_consumer_is_none_from_sds: Response
    ) -> None:
        expected = {
            "resourceType": "OperationOutcome",
            "issue": [
                {
                    "severity": "error",
                    "code": "exception",
                    "diagnostics": (
                        "No SDS org found for consumer ODS code ConsumerWithNoneInSDS"
                    ),
                }
            ],
        }
        assert response_when_consumer_is_none_from_sds.json() == expected

    def test_blank_consumer_asid_from_sds_returns_404_status_code(
        self, response_when_sds_returns_blank_consumer_asid: Response
    ) -> None:
        assert response_when_sds_returns_blank_consumer_asid.status_code == 404

    def test_blank_consumer_asid_from_sds_returns_no_asid_found_error(
        self, response_when_sds_returns_blank_consumer_asid: Response
    ) -> None:
        expected = {
            "resourceType": "OperationOutcome",
            "issue": [
                {
                    "severity": "error",
                    "code": "exception",
                    "diagnostics": (
                        "SDS result for consumer ODS code BlankAsidInSDS "
                        "did not contain a current ASID"
                    ),
                }
            ],
        }
        assert response_when_sds_returns_blank_consumer_asid.json() == expected

    @pytest.fixture
    def response_from_sending_request_with_empty_body(self, client: Client) -> Response:
        response = client.send_to_get_structured_record_endpoint(payload="")
        return response

    @pytest.fixture
    def response_from_requesting_patient_without_gp(
        self, get_structured_record_requester: Callable[[str], Response]
    ) -> Response:
        nhs_number_for_unregistered_patient = "9000000009"
        response = get_structured_record_requester(nhs_number_for_unregistered_patient)
        return response

    @pytest.fixture
    def response_when_sds_returns_no_provider(
        self, get_structured_record_requester: Callable[[str], Response]
    ) -> Response:
        nhs_number_for_patient_with_gp_not_in_sds = "9000000010"
        response = get_structured_record_requester(
            nhs_number_for_patient_with_gp_not_in_sds
        )
        return response

    @pytest.fixture
    def response_when_sds_returns_blank_provider_asid(
        self, get_structured_record_requester: Callable[[str], Response]
    ) -> Response:
        nhs_number_for_patient_with_gp_with_blank_provider_asid_in_sds = "9000000011"
        response = get_structured_record_requester(
            nhs_number_for_patient_with_gp_with_blank_provider_asid_in_sds
        )
        return response

    @pytest.fixture
    def response_when_sds_returns_blank_consumer_asid(
        self, client: Client, simple_request_payload: dict[str, Any]
    ) -> Response:
        ods_from_for_consumer_with_blank_consumer_asid_in_sds = "BlankAsidInSDS"
        headers = {"Ods-From": ods_from_for_consumer_with_blank_consumer_asid_in_sds}
        response = client.send_to_get_structured_record_endpoint(
            json.dumps(simple_request_payload), headers=headers
        )
        return response

    @pytest.fixture
    def response_when_provider_returns_error(
        self, get_structured_record_requester: Callable[[str], Response]
    ) -> Response:
        nhs_number_for_inducing_error_in_provider = "9000000012"
        response = get_structured_record_requester(
            nhs_number_for_inducing_error_in_provider
        )
        return response

    @pytest.fixture
    def response_when_nhs_number_does_not_exist(
        self, get_structured_record_requester: Callable[[str], Response]
    ) -> Response:
        nhs_number_that_does_not_exist = "1234567890"
        response = get_structured_record_requester(nhs_number_that_does_not_exist)
        return response

    @pytest.fixture
    def response_when_sds_provider_endpoint_blank(
        self, get_structured_record_requester: Callable[[str], Response]
    ) -> Response:
        nhs_number_for_patient_with_gp_with_blank_provider_endpoint = "9000000013"
        response = get_structured_record_requester(
            nhs_number_for_patient_with_gp_with_blank_provider_endpoint
        )
        return response

    @pytest.fixture
    def response_when_consumer_is_none_from_sds(
        self, client: Client, simple_request_payload: dict[str, Any]
    ) -> Response:
        ods_from_for_consumer_with_none_consumer_in_sds = "ConsumerWithNoneInSDS"
        headers = {"Ods-From": ods_from_for_consumer_with_none_consumer_in_sds}
        response = client.send_to_get_structured_record_endpoint(
            json.dumps(simple_request_payload), headers=headers
        )
        return response

    @pytest.fixture
    def get_structured_record_requester(
        self,
        client: Client,
        simple_request_payload: dict[str, Any],
    ) -> Callable[[str], Response]:
        def requester(nhs_number: str) -> Response:
            simple_request_payload["parameter"][0]["valueIdentifier"]["value"] = (
                nhs_number
            )
            response = client.send_to_get_structured_record_endpoint(
                json.dumps(simple_request_payload)
            )
            return response

        return requester
