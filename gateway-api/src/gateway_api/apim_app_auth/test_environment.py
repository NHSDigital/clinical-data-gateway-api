import base64
import os
from datetime import timedelta
from unittest.mock import MagicMock, patch

from gateway_api.apim_app_auth import environment
from gateway_api.apim_app_auth.config import Duration, DurationUnit
from gateway_api.apim_app_auth.http import SessionManager


class TestEnvironment:
    def setup_method(self) -> None:
        # Clear any set environment variables
        os.environ.clear()

    def test_session_manager(self) -> None:
        environment._session_manager = (  # noqa SLF001 - access private variable for testing purposes
            None  # reset session manager to force reinitialisation
        )

        os.environ["CLIENT_TIMEOUT"] = "30s"

        session_manager = environment.session_manager()
        assert session_manager._client_certificate is None  # noqa SLF001 - access private attribute for testing purposes

    def test_values(self) -> None:
        os.environ["CLIENT_TIMEOUT"] = "30s"
        os.environ["APIM_TOKEN_URL"] = "token_url"  # noqa S105 - dummy value
        os.environ["PDS_API_SECRET"] = base64.b64encode(b"private_key").decode("utf-8")
        os.environ["PDS_API_TOKEN"] = "api_key"  # noqa S105 - dummy value
        os.environ["APIM_TOKEN_EXPIRY_THRESHOLD"] = "60s"  # noqa S105 - dummy value
        os.environ["PDS_API_KID"] = "key_id"

        environ = environment.values()

        assert environ["client_timeout"].timedelta == timedelta(seconds=30)
        assert environ["apim_token_url"] == "token_url"  # noqa S105 - dummy value
        assert environ["apim_private_key"] == "private_key"
        assert environ["apim_api_key"] == "api_key"
        assert environ["apim_token_expiry_threshold"].timedelta == timedelta(seconds=60)
        assert environ["apim_key_id"] == "key_id"

    @patch("gateway_api.apim_app_auth.environment.values")
    @patch("gateway_api.apim_app_auth.environment.session_manager")
    def test_apim_authenticator(
        self,
        session_manager_mock: MagicMock,
        values_mock: MagicMock,
    ) -> None:
        expected_session_manager = SessionManager(client_timeout=timedelta(seconds=30))
        session_manager_mock.return_value = expected_session_manager

        environ: environment.Environment = {
            "apim_private_key": "private_key",
            "apim_api_key": "api_key",
            "apim_key_id": "key_id",
            "apim_token_expiry_threshold": Duration(DurationUnit.SECONDS, 60),
            "apim_token_url": "token_url",
            "client_timeout": Duration(DurationUnit.SECONDS, 30),
        }

        values_mock.return_value = environ

        apim_authenticator = environment.apim_authenticator()
        assert apim_authenticator._private_key == "private_key"  # noqa SLF001 - access private attribute for testing purposes
        assert apim_authenticator._api_key == "api_key"  # noqa SLF001
        assert apim_authenticator._key_id == "key_id"  # noqa SLF001
        assert apim_authenticator._token_validity_threshold == timedelta(seconds=60)  # noqa SLF001
        assert apim_authenticator._token_endpoint == "token_url"  # noqa SLF001
        assert apim_authenticator._session_manager == expected_session_manager  # noqa SLF001
