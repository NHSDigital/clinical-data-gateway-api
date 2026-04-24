import os
from datetime import timedelta
from unittest.mock import MagicMock, call, patch

from gateway_api.apim_app_auth import environment
from gateway_api.apim_app_auth.config import Duration, DurationUnit
from gateway_api.apim_app_auth.http import SessionManager


class TestEnvironment:
    def setup_method(self) -> None:
        # Clear any set environment variables
        os.environ.clear()

    @patch("gateway_api.apim_app_auth.environment.parameters.get_secret")
    def test_session_manager_with_mtls(self, get_secret_mock: MagicMock) -> None:
        environment._session_manager = (  # noqa SLF001 - access private variable for testing purposes
            None  # reset session manager to force reinitialisation
        )

        get_secret_mock.side_effect = lambda secret_name: {
            "mtls_cert_name": "mtls_cert",
            "mtls_key_name": "mtls_key",
        }[secret_name]

        os.environ["APIM_MTLS_CERT_NAME"] = "mtls_cert_name"
        os.environ["APIM_MTLS_KEY_NAME"] = "mtls_key_name"
        os.environ["CLIENT_TIMEOUT"] = "30s"

        certificate_name = "mtls_cert_name"
        key_name = "mtls_key_name"

        session_manager = environment.session_manager()
        client_certificate = session_manager._client_certificate  # noqa SLF001 - access private attribute for testing purposes

        assert client_certificate == {
            "certificate": "mtls_cert",
            "key": "mtls_key",
        }

        get_secret_mock.assert_has_calls([call(certificate_name), call(key_name)])

    @patch("gateway_api.apim_app_auth.environment.parameters.get_secret")
    def test_session_manager(self, get_secret_mock: MagicMock) -> None:
        environment._session_manager = (  # noqa SLF001 - access private variable for testing purposes
            None  # reset session manager to force reinitialisation
        )

        os.environ["CLIENT_TIMEOUT"] = "30s"

        session_manager = environment.session_manager()
        assert session_manager._client_certificate is None  # noqa SLF001 - access private attribute for testing purposes

        get_secret_mock.assert_not_called()

    def test_values(self) -> None:
        os.environ["CLIENT_TIMEOUT"] = "30s"
        os.environ["APIM_TOKEN_URL"] = "token_url"  # noqa S105 - dummy value
        os.environ["APIM_PRIVATE_KEY_NAME"] = "private_key_name"
        os.environ["APIM_API_KEY_NAME"] = "api_key_name"
        os.environ["APIM_TOKEN_EXPIRY_THRESHOLD"] = "60s"  # noqa S105 - dummy value
        os.environ["APIM_KEY_ID"] = "key_id"
        os.environ["PDM_BUNDLE_URL"] = "pdm_url"
        os.environ["MNS_EVENT_URL"] = "mns_url"

        environ = environment.values()

        assert environ["client_timeout"].timedelta == timedelta(seconds=30)
        assert environ["apim_token_url"] == "token_url"  # noqa S105 - dummy value
        assert environ["apim_private_key_name"] == "private_key_name"
        assert environ["apim_api_key_name"] == "api_key_name"
        assert environ["apim_token_expiry_threshold"].timedelta == timedelta(seconds=60)
        assert environ["apim_key_id"] == "key_id"
        assert environ["pdm_url"] == "pdm_url"
        assert environ["mns_url"] == "mns_url"

    @patch("gateway_api.apim_app_auth.environment.parameters.get_secret")
    @patch("gateway_api.apim_app_auth.environment.values")
    @patch("gateway_api.apim_app_auth.environment.session_manager")
    def test_apim_authenticator(
        self,
        session_manager_mock: MagicMock,
        values_mock: MagicMock,
        get_secret_mock: MagicMock,
    ) -> None:
        expected_session_manager = SessionManager(client_timeout=timedelta(seconds=30))
        session_manager_mock.return_value = expected_session_manager

        environ: environment.Environment = {
            "apim_private_key_name": "private_key_name",
            "apim_api_key_name": "api_key_name",
            "apim_key_id": "key_id",
            "apim_token_expiry_threshold": Duration(DurationUnit.SECONDS, 60),
            "apim_token_url": "token_url",
            "client_timeout": Duration(DurationUnit.SECONDS, 30),
            "pdm_url": "pdm_url",
            "mns_url": "mns_url",
        }

        values_mock.return_value = environ

        get_secret_mock.side_effect = lambda secret_name: {
            "private_key_name": "private_key",
            "api_key_name": "api_key",
        }[secret_name]

        apim_authenticator = environment.apim_authenticator()
        assert apim_authenticator._private_key == "private_key"  # noqa SLF001 - access private attribute for testing purposes
        assert apim_authenticator._api_key == "api_key"  # noqa SLF001
        assert apim_authenticator._key_id == "key_id"  # noqa SLF001
        assert apim_authenticator._token_validity_threshold == timedelta(seconds=60)  # noqa SLF001
        assert apim_authenticator._token_endpoint == "token_url"  # noqa SLF001
        assert apim_authenticator._session_manager == expected_session_manager  # noqa SLF001
