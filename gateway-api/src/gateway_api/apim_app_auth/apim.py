import functools
import logging
import os
import uuid
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any, TypedDict

import jwt
import requests
from stubs.apim_app_auth.stub import APIMAppAuthStub

from gateway_api.apim_app_auth.http import RequestMethod, SessionManager

_logger = logging.getLogger(__name__)


# TODO [GPCAPIM-359]: change this to a new STUB_APIM_APP_AUTH env var
_pds_url = os.getenv("APIM_TOKEN_URL", "not stub")
STUB_APIM_APP_AUTH = _pds_url.strip().lower() == "stub"


def _make_session_post(
    session: requests.Session, endpoint: str, data: dict[str, str]
) -> requests.Response:
    print("DaveW: in _make_session_post STUB_APIM_APP_AUTH", STUB_APIM_APP_AUTH)
    if not STUB_APIM_APP_AUTH:
        print("DaveW: in if ", session.post)
        return session.post(endpoint, data=data)
    else:
        stub = APIMAppAuthStub()
        print("Dave W: in _make_session_post, stub:", stub.session_post)
        print(
            "Dave W: in _make_session_post, session_post:",
            stub.session_post(session, endpoint, data),
        )
        response = stub.session_post(session, endpoint, data)
        return response


class ApimAuthenticationException(Exception):
    pass


class ApimAuthenticator:
    class __AccessToken(TypedDict):
        value: str
        expiry: datetime

    def __init__(
        self,
        private_key: str,
        key_id: str,
        api_key: str,
        token_validity_threshold: timedelta,
        token_endpoint: str,
        session_manager: SessionManager,
    ):
        self._private_key = private_key
        self._key_id = key_id
        self._api_key = api_key
        self._token_validity_threshold = token_validity_threshold
        self._token_endpoint = token_endpoint
        self._session_manager = session_manager

        self._access_token: ApimAuthenticator.__AccessToken | None = None

    def auth[**P, S](self, func: RequestMethod[P, S]) -> Callable[P, S]:
        """
        Decorate a given function with APIM authentication. This authentication will be
        provided via a `requests.Session` object.
        """

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            @self._session_manager.with_session
            def with_session(
                session: requests.Session, access_token: ApimAuthenticator.__AccessToken
            ) -> S:
                session.headers.update(
                    {"Authorization": f"Bearer {access_token['value']}"}
                )
                return func(session, *args, **kwargs)

            # If there isn't an access token yet, or the token will expire within the
            # token validity threshold, reauthenticate.
            if (
                self._access_token is None
                or self._access_token["expiry"] - datetime.now(tz=timezone.utc)
                < self._token_validity_threshold
            ):
                _logger.debug("Authenticating with APIM...")
                self._access_token = self._authenticate()

            return with_session(self._access_token)

        return wrapper

    def _create_client_assertion(self) -> str:
        _logger.debug("Creating client assertion JWT for APIM authentication")
        claims = {
            "sub": self._api_key,
            "iss": self._api_key,
            "jti": str(uuid.uuid4()),
            "aud": self._token_endpoint,
            "exp": int(
                (datetime.now(tz=timezone.utc) + timedelta(seconds=30)).timestamp()
            ),
        }
        _logger.debug(
            "Created client claims. jti: %s, exp: %s, aud: %s",
            claims["jti"],
            claims["exp"],
            claims["aud"],
        )

        client_assertion = jwt.encode(
            claims,
            self._private_key,
            algorithm="RS512",
            headers={"kid": self._key_id},
        )

        _logger.debug("Created client assertion. kid: %s", self._key_id)

        return client_assertion

    def _authenticate(self) -> __AccessToken:
        @self._session_manager.with_session
        def with_session(session: requests.Session) -> ApimAuthenticator.__AccessToken:
            client_assertion = self._create_client_assertion()

            _logger.debug("Sending token request with created session.")

            response = _make_session_post(
                session,
                self._token_endpoint,
                data={
                    "grant_type": "client_credentials",
                    "client_assertion_type": "urn:ietf:params:oauth"
                    ":client-assertion-type:jwt-bearer",
                    "client_assertion": client_assertion,
                },
            )

            _logger.debug(
                "Response received from APIM token endpoint. Status code: %s",
                response.status_code,
            )

            if response.status_code != 200:
                raise ApimAuthenticationException(
                    f"Failed to authenticate with APIM. "
                    f"Status code: {response.status_code}"
                    f", Response: {response.text}"
                )

            response_data = response.json()
            _logger.debug(
                "APIM authentication successful. Expiry: %s",
                response_data["expires_in"],
            )

            return {
                "value": response_data["access_token"],
                "expiry": datetime.now(tz=timezone.utc)
                + timedelta(seconds=int(response_data["expires_in"])),
            }

        _logger.debug(
            "Sending authentication request to APIM: %s", self._token_endpoint
        )
        return with_session()
