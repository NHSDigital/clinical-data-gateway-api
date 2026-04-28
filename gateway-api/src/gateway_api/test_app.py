"""Unit tests for the Flask app endpoints."""

import json
from collections.abc import Generator
from copy import copy
from typing import Any
from unittest.mock import Mock

import pytest
from flask import Flask
from flask.testing import FlaskClient
from pytest_mock import MockerFixture

from gateway_api.app import (
    app,
    configure_app,
    get_env_var,
    log_env_vars,
    start_app,
)
from gateway_api.conftest import ScopedEnvVars


@pytest.fixture
def client() -> Generator[FlaskClient[Flask]]:
    with ScopedEnvVars(
        {
            "FLASK_HOST": "localhost",
            "FLASK_PORT": "5000",
            "PDS_URL": "https://test-pds-url",
            "SDS_URL": "https://test-sds-url",
        }
    ):
        configure_app(app)
        app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestAppInitialization:
    def test_get_env_var_when_env_var_is_set(self) -> None:
        with ScopedEnvVars({"FLASK_HOST": "host_is_set"}):
            actual = get_env_var("FLASK_HOST", str)
            assert actual == "host_is_set"

    def test_get_env_var_raises_runtime_error_if_env_var_not_set(self) -> None:
        with ScopedEnvVars({"FLASK_HOST": None}), pytest.raises(RuntimeError):
            _ = get_env_var("FLASK_HOST", str)

    def test_get_env_var_raises_runtime_error_if_loader_fails(self) -> None:
        with ScopedEnvVars({"FLASK_PORT": "not_an_int"}), pytest.raises(RuntimeError):
            _ = get_env_var("FLASK_PORT", int)

    def test_configure_app(self) -> None:
        test_app = Mock()
        config = {
            "FLASK_HOST": "test_host",
            "FLASK_PORT": "1234",
            "PDS_URL": "test_pds_url",
            "SDS_URL": "test_sds_url",
        }

        with ScopedEnvVars(config):
            configure_app(test_app)

        expected = {
            "FLASK_HOST": "test_host",
            "FLASK_PORT": 1234,
            "PDS_URL": "test_pds_url",
            "SDS_URL": "test_sds_url",
        }
        test_app.config.update.assert_called_with(expected)

    def test_logging_environment_variables_on_app_initialization(
        self, mocker: MockerFixture
    ) -> None:
        log_mock_info = mocker.patch("gateway_api.app._logger.info")

        config = {
            "FLASK_HOST": "test_host",
            "FLASK_PORT": "1234",
            "PDS_URL": "test_pds_url",
            "SDS_URL": "test_sds_url",
        }
        with ScopedEnvVars(config):
            log_env_vars()

        # Check that the environment variables were logged
        log_mock_info.assert_called_with(
            {
                "description": "Initializing Flask app",
                "env_vars": config,
            }
        )

    def test_start_app_logs_startup_details(self) -> None:
        test_app = Mock()
        test_app.config = {}

        test_env_vars = {
            "FLASK_HOST": "test_host",
            "FLASK_PORT": "1234",
            "PDS_URL": "https://test-pds-url",
            "SDS_URL": "https://test-sds-url",
        }

        with ScopedEnvVars(test_env_vars):
            start_app(test_app)

            test_app.run.assert_called_with(host="test_host", port=1234)


class TestGetStructuredRecord:
    @pytest.mark.usefixtures("mock_positive_return_value_from_controller_run")
    def test_valid_get_structured_record_request_returns_expected_bundle(
        self,
        get_structured_record_response: Flask,
        valid_simple_response_payload: dict[str, Any],
    ) -> None:
        actual_bundle = get_structured_record_response.get_json()
        assert actual_bundle == valid_simple_response_payload

    @pytest.mark.usefixtures("mock_positive_return_value_from_controller_run")
    def test_valid_get_structured_record_request_returns_200(
        self,
        get_structured_record_response: Flask,
    ) -> None:
        assert get_structured_record_response.status_code == 200

    @pytest.mark.usefixtures("mock_raise_error_from_controller_run")
    def test_get_structured_record_returns_500_when_an_uncaught_exception_is_raised(
        self,
        get_structured_record_response: Flask,
    ) -> None:
        actual_status_code = get_structured_record_response.status_code
        assert actual_status_code == 500

    @staticmethod
    @pytest.fixture
    def missing_headers(
        request: pytest.FixtureRequest, valid_headers: dict[str, str]
    ) -> dict[str, str]:
        invalid_headers = copy(valid_headers)
        del invalid_headers[request.param]
        return invalid_headers

    @pytest.mark.parametrize(
        "missing_headers",
        ["ODS-from", "Ssp-TraceID"],
        indirect=True,
    )
    @pytest.mark.usefixtures("missing_headers")
    def test_get_structured_record_returns_400_when_required_header_missing(
        self,
        get_structured_record_response_from_missing_header: Flask,
    ) -> None:
        assert get_structured_record_response_from_missing_header.status_code == 400

    @pytest.mark.parametrize(
        "missing_headers",
        ["ODS-from", "Ssp-TraceID"],
        indirect=True,
    )
    @pytest.mark.usefixtures("missing_headers")
    def test_get_structured_record_returns_fhir_content_when_missing_header(
        self,
        get_structured_record_response_from_missing_header: Flask,
    ) -> None:
        assert (
            "application/fhir+json"
            in get_structured_record_response_from_missing_header.content_type
        )

    @pytest.mark.parametrize(
        ("missing_headers", "expected_message"),
        [
            pytest.param(
                "ODS-from",
                'Missing or empty required header "ODS-from"',
            ),
            pytest.param(
                "Ssp-TraceID",
                'Missing or empty required header "Ssp-TraceID"',
            ),
        ],
        indirect=["missing_headers"],
    )
    def test_get_structured_record_returns_operation_outcome_when_missing_header(
        self,
        get_structured_record_response_from_missing_header: Flask,
        expected_message: str,
    ) -> None:
        expected_body = {
            "resourceType": "OperationOutcome",
            "issue": [
                {
                    "severity": "error",
                    "code": "exception",
                    "diagnostics": expected_message,
                }
            ],
        }
        assert (
            expected_body
            == get_structured_record_response_from_missing_header.get_json()
        )

    def test_get_structured_record_returns_400_when_invalid_json_sent(
        self, get_structured_record_response_using_invalid_json_body: Flask
    ) -> None:
        assert get_structured_record_response_using_invalid_json_body.status_code == 400

    def test_get_structured_record_returns_content_type_fhir_json_for_invalid_json_sent(
        self, get_structured_record_response_using_invalid_json_body: Flask
    ) -> None:
        assert (
            "application/fhir+json"
            in get_structured_record_response_using_invalid_json_body.content_type
        )

    def test_get_structured_record_returns_internal_server_error_when_invalid_json_sent(
        self, get_structured_record_response_using_invalid_json_body: Flask
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
        actual = get_structured_record_response_using_invalid_json_body.get_json()
        assert actual == expected

    @staticmethod
    @pytest.fixture
    def get_structured_record_response(
        client: FlaskClient[Flask],
        valid_headers: dict[str, str],
        valid_simple_request_payload: dict[str, Any],
    ) -> Flask:
        response = client.post(
            "/patient/$gpc.getstructuredrecord",
            json=valid_simple_request_payload,
            headers=valid_headers,
        )
        return response

    @staticmethod
    @pytest.fixture
    def get_structured_record_response_from_missing_header(
        client: FlaskClient[Flask],
        missing_headers: dict[str, str],
        valid_simple_request_payload: dict[str, Any],
    ) -> Flask:
        response = client.post(
            "/patient/$gpc.getstructuredrecord",
            data=json.dumps(valid_simple_request_payload),
            headers=missing_headers,
        )
        return response

    @staticmethod
    @pytest.fixture
    def get_structured_record_response_using_invalid_json_body(
        client: FlaskClient[Flask],
        valid_headers: dict[str, str],
    ) -> Flask:
        invalid_json = "invalid json data"

        response = client.post(
            "/patient/$gpc.getstructuredrecord",
            data=invalid_json,
            headers=valid_headers,
        )
        return response

    @staticmethod
    @pytest.fixture
    def mock_positive_return_value_from_controller_run(
        mocker: MockerFixture,
        valid_headers: dict[str, str],
        valid_simple_response_payload: dict[str, Any],
    ) -> None:
        positive_response = Mock()
        positive_response.status_code = 200
        positive_response.json.return_value = valid_simple_response_payload
        positive_response.headers = valid_headers

        mocker.patch(
            "gateway_api.controller.Controller.run", return_value=positive_response
        )

    @staticmethod
    @pytest.fixture
    def mock_raise_error_from_controller_run(
        mocker: MockerFixture,
    ) -> None:
        internal_error = ValueError("Test exception")
        mocker.patch(
            "gateway_api.controller.Controller.run", side_effect=internal_error
        )


class TestHealthCheck:
    def test_health_check_returns_200_and_healthy_status(
        self, client: FlaskClient[Flask]
    ) -> None:
        response = client.get("/health")

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "healthy"

    @pytest.mark.parametrize("method", ["POST", "PUT", "DELETE", "PATCH"])
    def test_health_check_only_accepts_get_method(
        self, client: FlaskClient[Flask], method: str
    ) -> None:
        """Test that health_check only accepts GET method."""
        response = client.open("/health", method=method)
        assert response.status_code == 405
