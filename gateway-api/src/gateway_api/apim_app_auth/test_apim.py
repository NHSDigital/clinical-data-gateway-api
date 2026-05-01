from collections.abc import Callable, Generator
from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests
from jwt import InvalidKeyError

from gateway_api.apim_app_auth.apim import (
    ApimAuthenticationException,
    ApimAuthenticator,
)
from gateway_api.apim_app_auth.request_context import (
    reset_correlation_id,
    set_correlation_id,
)


class TestApimAuthenticator:
    @pytest.fixture(autouse=True)
    def set_correlation_id_for_logger(self) -> Generator[None, None, None]:
        set_correlation_id(
            full_id="test_id_long",
            short_id="test_id",
        )
        yield
        reset_correlation_id()

    def setup_method(self) -> None:
        self.mock_session = Mock()

    def mock_with_session(self, func: Callable[..., Any]) -> Callable[..., Any]:

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(self.mock_session, *args, **kwargs)

        return wrapper

    @patch("gateway_api.apim_app_auth.apim.APIMAppAuthStub")
    @patch("gateway_api.apim_app_auth.apim.jwt.encode")
    def test_auth(
        self, mock_jwt: MagicMock, mock_apmim_app_auth_stub: MagicMock
    ) -> None:
        expected_client_assertion = "client_assertion"
        mock_jwt.return_value = expected_client_assertion

        expected_access_token = "access_token"  # noqa S105 - Dummy value
        expected_expires_in = timedelta(seconds=5)

        (
            mock_apmim_app_auth_stub.return_value.session_post.return_value.json.return_value
        ) = {
            "access_token": expected_access_token,
            "expires_in": expected_expires_in.total_seconds(),
        }
        mock_apmim_app_auth_stub.return_value.session_post.return_value.status_code = (
            200
        )

        expected_api_key = "api_key"
        expected_token_endpoint = "token_endpoint"  # noqa S106 - Dummy value
        expected_key_id = "key_id"
        apim_authenticator = ApimAuthenticator(
            private_key="private_key",
            key_id=expected_key_id,
            api_key=expected_api_key,
            token_validity_threshold=timedelta(minutes=5),
            token_endpoint=expected_token_endpoint,
            session_manager=Mock(),
        )

        @apim_authenticator.auth
        def method(_: requests.Session) -> None:
            self.mock_session.headers.update.assert_called_once_with(
                {"Authorization": f"Bearer {expected_access_token}"}
            )

            mock_jwt.assert_called_once()
            args, kwargs = mock_jwt.call_args

            provided_claims = args[0]
            assert provided_claims["sub"] == expected_api_key
            assert provided_claims["iss"] == expected_api_key
            assert provided_claims["aud"] == expected_token_endpoint
            assert provided_claims["jti"] is not None
            assert provided_claims["exp"] < int(
                (datetime.now(tz=timezone.utc) + timedelta(seconds=31)).timestamp()
            )

            assert kwargs == {"algorithm": "RS512", "headers": {"kid": expected_key_id}}

            # SLF001: Private access to support testing
            stored_access_token = apim_authenticator._access_token  # noqa SLF001
            assert stored_access_token is not None
            assert stored_access_token["value"] == expected_access_token
            assert stored_access_token["expiry"] < (
                datetime.now(tz=timezone.utc) + expected_expires_in
            )

        method()

    @patch("gateway_api.apim_app_auth.http.SessionManager")
    @patch("gateway_api.apim_app_auth.apim.jwt.encode")
    def test_auth_existing_valid_token(
        self, mock_jwt: MagicMock, mock_session_manager: MagicMock
    ) -> None:
        mock_session_manager.with_session = self.mock_with_session

        apim_authenticator = ApimAuthenticator(
            private_key="private_key",
            key_id="key_id",
            api_key="api_key",
            token_validity_threshold=timedelta(minutes=5),
            token_endpoint="token_endpoint",  # noqa S106 - Dummy value
            session_manager=mock_session_manager,
        )

        expected_access_token = "access_token"  # noqa S105 - Dummy value
        apim_authenticator._access_token = {  # noqa SLF001 - Private access to support testing
            "value": expected_access_token,
            "expiry": datetime.now(tz=timezone.utc) + timedelta(minutes=10),
        }

        @apim_authenticator.auth
        def method(_: requests.Session) -> None:
            self.mock_session.headers.update.assert_called_once_with(
                {"Authorization": f"Bearer {expected_access_token}"}
            )

            mock_jwt.assert_not_called()

        method()

    @patch("gateway_api.apim_app_auth.apim.APIMAppAuthStub")
    @patch("gateway_api.apim_app_auth.apim.jwt.encode")
    def test_auth_existing_invalid_token(
        self, mock_jwt: MagicMock, mock_apmim_app_auth_stub: MagicMock
    ) -> None:
        expected_client_assertion = "client_assertion"
        mock_jwt.return_value = expected_client_assertion

        expected_access_token = "access_token"  # noqa S105 - Dummy value
        expected_expires_in = timedelta(seconds=5)

        (
            mock_apmim_app_auth_stub.return_value.session_post.return_value.json.return_value
        ) = {
            "access_token": expected_access_token,
            "expires_in": expected_expires_in.total_seconds(),
        }
        mock_apmim_app_auth_stub.return_value.session_post.return_value.status_code = (
            200
        )

        expected_api_key = "api_key"
        expected_token_endpoint = "token_endpoint"  # noqa S106 - Dummy value
        expected_key_id = "key_id"
        apim_authenticator = ApimAuthenticator(
            private_key="private_key",
            key_id=expected_key_id,
            api_key=expected_api_key,
            token_validity_threshold=timedelta(minutes=5),
            token_endpoint=expected_token_endpoint,
            session_manager=Mock(),
        )

        apim_authenticator._access_token = {  # noqa SLF001 - Private access to support testing
            "value": "old_access_token",
            "expiry": datetime.now(tz=timezone.utc) - timedelta(seconds=1),
        }

        @apim_authenticator.auth
        def method(_: requests.Session) -> None:
            self.mock_session.headers.update.assert_called_once_with(
                {"Authorization": f"Bearer {expected_access_token}"}
            )

            mock_jwt.assert_called_once()
            args, kwargs = mock_jwt.call_args

            provided_claims = args[0]
            assert provided_claims["sub"] == expected_api_key
            assert provided_claims["iss"] == expected_api_key
            assert provided_claims["aud"] == expected_token_endpoint
            assert provided_claims["jti"] is not None
            assert provided_claims["exp"] < int(
                (datetime.now(tz=timezone.utc) + timedelta(seconds=31)).timestamp()
            )

            assert kwargs == {"algorithm": "RS512", "headers": {"kid": expected_key_id}}

            # SLF001: Private access to support testing
            stored_access_token = apim_authenticator._access_token  # noqa SLF001
            assert stored_access_token is not None
            assert stored_access_token["value"] == expected_access_token
            assert stored_access_token["expiry"] < (
                datetime.now(tz=timezone.utc) + expected_expires_in
            )

        method()

    @patch("gateway_api.apim_app_auth.apim.APIMAppAuthStub")
    @patch("gateway_api.apim_app_auth.http.SessionManager")
    @patch("gateway_api.apim_app_auth.apim.jwt.encode")
    def test_auth_unsuccessful_status_code(
        self,
        mock_jwt: MagicMock,
        mock_session_manager: MagicMock,
        mock_apim_app_auth_stub: MagicMock,
    ) -> None:
        mock_session_manager.with_session = self.mock_with_session

        mock_jwt.return_value = "client_assertion"

        mock_apim_app_auth_stub.return_value.session_post.return_value.status_code = 401
        mock_apim_app_auth_stub.return_value.session_post.return_value.text = (
            "Unauthorized"
        )

        # self.mock_session.post.return_value.status_code = 401
        # self.mock_session.post.return_value.text = "Unauthorized"

        apim_authenticator = ApimAuthenticator(
            private_key="private_key",
            key_id="key_id",
            api_key="api_key",
            token_validity_threshold=timedelta(minutes=5),
            token_endpoint="token_endpoint",  # noqa S106 - Dummy value
            session_manager=mock_session_manager,
        )

        @apim_authenticator.auth
        def method(_: requests.Session) -> None:
            """Dummy method just to apply the auth decorator"""
            pass

        with pytest.raises(ApimAuthenticationException):
            method()

    @patch("gateway_api.apim_app_auth.apim.APIMAppAuthStub")
    @patch("gateway_api.apim_app_auth.http.SessionManager")
    @patch("gateway_api.apim_app_auth.apim.jwt.encode")
    def test_auth_session_post_raises_exception(
        self,
        mock_jwt: MagicMock,
        mock_session_manager: MagicMock,
        mock_apim_app_auth_stub: MagicMock,
    ) -> None:
        mock_session_manager.with_session = self.mock_with_session

        mock_jwt.return_value = "client_assertion"

        mock_apim_app_auth_stub.return_value.session_post.side_effect = (
            requests.RequestException("Connection failed")
        )

        apim_authenticator = ApimAuthenticator(
            private_key="private_key",
            key_id="key_id",
            api_key="api_key",
            token_validity_threshold=timedelta(minutes=5),
            token_endpoint="token_endpoint",  # noqa S106 - Dummy value
            session_manager=mock_session_manager,
        )

        @apim_authenticator.auth
        def method(_: requests.Session) -> None:
            """Dummy method just to apply the auth decorator"""
            pass

        with pytest.raises(requests.RequestException, match="Connection failed"):
            method()

    @patch("gateway_api.apim_app_auth.http.SessionManager")
    @patch("gateway_api.apim_app_auth.apim.jwt.encode")
    def test_auth_jwt_encode_raises_exception(
        self, mock_jwt: MagicMock, mock_session_manager: MagicMock
    ) -> None:
        mock_session_manager.with_session = self.mock_with_session

        mock_jwt.side_effect = InvalidKeyError("JWT encoding failed")

        apim_authenticator = ApimAuthenticator(
            private_key="private_key",
            key_id="key_id",
            api_key="api_key",
            token_validity_threshold=timedelta(minutes=5),
            token_endpoint="token_endpoint",  # noqa S106 - Dummy value
            session_manager=mock_session_manager,
        )

        @apim_authenticator.auth
        def method(_: requests.Session) -> None:
            """Dummy method just to apply the auth decorator"""
            pass

        with pytest.raises(InvalidKeyError, match="JWT encoding failed"):
            method()
