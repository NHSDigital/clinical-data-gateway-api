"""Unit tests for call_gateway.py script."""

import json
import sys
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest
import requests
from call_gateway import main


class TestCallGateway:
    """Test suite for the call_gateway script."""

    def test_successful_request(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful POST request with valid NHS number."""
        nhs_number = "9690937278"
        base_url = "https://example.com"
        monkeypatch.setenv("BASE_URL", base_url)
        monkeypatch.setattr(sys, "argv", ["call_gateway.py", nhs_number])

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"resourceType": "Bundle"}

        captured_output = StringIO()

        with (
            patch("requests.post", return_value=mock_response) as mock_post,
            patch("sys.stdout", captured_output),
        ):
            main()

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args.args[0] == f"{base_url}/patient/$gpc.getstructuredrecord"
        assert call_args.kwargs["headers"]["Content-Type"] == "application/fhir+json"
        assert call_args.kwargs["headers"]["Accept"] == "application/fhir+json"
        assert call_args.kwargs["headers"]["Ods-From"] == "S44444"
        assert "Ssp-TraceID" in call_args.kwargs["headers"]
        assert call_args.kwargs["json"]["resourceType"] == "Parameters"
        assert (
            call_args.kwargs["json"]["parameter"][0]["valueIdentifier"]["value"]
            == nhs_number
        )
        assert call_args.kwargs["timeout"] == 10

        output = captured_output.getvalue()
        assert "Status Code: 200" in output
        assert "Response:" in output

    def test_missing_base_url_environment_variable(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test error handling when BASE_URL environment variable is not set."""
        monkeypatch.delenv("BASE_URL", raising=False)
        monkeypatch.setattr(sys, "argv", ["call_gateway.py", "9690937278"])

        captured_output = StringIO()
        with (
            patch("sys.stdout", captured_output),
            pytest.raises(SystemExit) as exc_info,
        ):
            main()

        assert exc_info.value.code == 1
        output = captured_output.getvalue()
        assert "Error: BASE_URL environment variable is not set" in output

    def test_http_error_with_response_body(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test handling of HTTP error with response body."""
        nhs_number = "9690937278"
        monkeypatch.setenv("BASE_URL", "https://example.com")
        monkeypatch.setattr(sys, "argv", ["call_gateway.py", nhs_number])

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"

        http_error = requests.exceptions.HTTPError("HTTP Error")
        http_error.response = mock_response

        captured_output = StringIO()

        with patch("requests.post") as mock_post:
            mock_post.return_value.raise_for_status.side_effect = http_error
            with (
                patch("sys.stdout", captured_output),
                pytest.raises(SystemExit) as exc_info,
            ):
                main()

        assert exc_info.value.code == 1
        output = captured_output.getvalue()
        assert "Error:" in output
        assert "Status Code: 400" in output
        assert "Response Body: Bad Request" in output

    def test_request_payload_structure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that request payload has correct FHIR structure."""
        nhs_number = "9690937278"
        monkeypatch.setenv("BASE_URL", "https://example.com")
        monkeypatch.setattr(sys, "argv", ["call_gateway.py", nhs_number])

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"resourceType": "Bundle"}

        with (
            patch("requests.post", return_value=mock_response) as mock_post,
            patch("sys.stdout", StringIO()),
        ):
            main()

        call_args = mock_post.call_args
        payload = call_args.kwargs["json"]
        assert payload["resourceType"] == "Parameters"
        assert len(payload["parameter"]) == 1
        assert payload["parameter"][0]["name"] == "patientNHSNumber"
        assert (
            payload["parameter"][0]["valueIdentifier"]["system"]
            == "https://fhir.nhs.uk/Id/nhs-number"
        )
        assert payload["parameter"][0]["valueIdentifier"]["value"] == nhs_number

    def test_request_headers(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that request headers are correctly set."""
        nhs_number = "9690937278"
        monkeypatch.setenv("BASE_URL", "https://example.com")
        monkeypatch.setattr(sys, "argv", ["call_gateway.py", nhs_number])

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"resourceType": "Bundle"}

        with (
            patch("requests.post", return_value=mock_response) as mock_post,
            patch("sys.stdout", StringIO()),
        ):
            main()

        call_args = mock_post.call_args
        headers = call_args.kwargs["headers"]
        assert headers["Content-Type"] == "application/fhir+json"
        assert headers["Accept"] == "application/fhir+json"
        assert headers["Ods-From"] == "S44444"
        assert "Ssp-TraceID" in headers
        # Verify Ssp-TraceID is a valid UUID format
        trace_id = headers["Ssp-TraceID"]
        assert len(trace_id) == 36
        assert trace_id.count("-") == 4

    def test_url_construction(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that URL is correctly constructed from BASE_URL."""
        base_url = "https://test.example.com"
        nhs_number = "9690937278"
        monkeypatch.setenv("BASE_URL", base_url)
        monkeypatch.setattr(sys, "argv", ["call_gateway.py", nhs_number])

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"resourceType": "Bundle"}

        with (
            patch("requests.post", return_value=mock_response) as mock_post,
            patch("sys.stdout", StringIO()),
        ):
            main()

        call_args = mock_post.call_args
        assert call_args.args[0] == f"{base_url}/patient/$gpc.getstructuredrecord"

    def test_output_format_for_successful_response(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test output format for successful response includes status and JSON."""
        nhs_number = "9690937278"
        monkeypatch.setenv("BASE_URL", "https://example.com")
        monkeypatch.setattr(sys, "argv", ["call_gateway.py", nhs_number])

        expected_json = {"resourceType": "Bundle", "id": "test-bundle"}
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_json

        captured_output = StringIO()

        with (
            patch("requests.post", return_value=mock_response),
            patch("sys.stdout", captured_output),
        ):
            main()

        output = captured_output.getvalue()
        assert "Status Code: 200" in output
        assert "Response:" in output
        # Verify JSON is properly formatted
        assert json.dumps(expected_json, indent=2) in output
