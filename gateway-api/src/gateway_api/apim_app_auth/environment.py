import base64
from typing import TypedDict

from gateway_api.apim_app_auth.apim import ApimAuthenticator
from gateway_api.apim_app_auth.config import (
    Duration,
    get_environment_variable,
)
from gateway_api.apim_app_auth.http import SessionManager

__all__ = [
    "apim_authenticator",
    "values",
    "session_manager",
]


class Environment(TypedDict):
    client_timeout: Duration
    apim_token_url: str
    apim_api_key: str
    apim_token_expiry_threshold: Duration
    apim_key_id: str
    apim_private_key: str


_environment: Environment | None = None
_session_manager: SessionManager | None = None
_apim_authenticator: ApimAuthenticator | None = None


def values() -> Environment:
    global _environment
    if _environment is None:
        decoded_private_key = (
            base64.b64decode(get_environment_variable("PDS_API_SECRET", str))
            .decode("utf-8")
            .replace("\\n", "\n")
            .strip()
        )
        _environment = Environment(
            client_timeout=get_environment_variable(
                "CLIENT_TIMEOUT",
                Duration,
            ),
            apim_token_url=get_environment_variable(
                "APIM_TOKEN_URL",
                str,
            ),
            apim_api_key=get_environment_variable(
                "PDS_API_TOKEN",
                str,
            ),
            apim_token_expiry_threshold=get_environment_variable(
                "APIM_TOKEN_EXPIRY_THRESHOLD",
                Duration,
            ),
            apim_key_id=get_environment_variable(
                "PDS_API_KID",
                str,
            ),
            apim_private_key=decoded_private_key,
        )

    return _environment


def session_manager() -> SessionManager:
    global _session_manager

    if _session_manager is None:
        client_certificate = None

        _session_manager = SessionManager(
            client_timeout=get_environment_variable(
                "CLIENT_TIMEOUT", Duration
            ).timedelta,
            client_certificate=client_certificate,
        )

    return _session_manager


def apim_authenticator() -> ApimAuthenticator:
    global _apim_authenticator

    if _apim_authenticator is None:
        env = values()
        _apim_authenticator = ApimAuthenticator(
            private_key=env["apim_private_key"],
            key_id=env["apim_key_id"],
            api_key=env["apim_api_key"],
            token_endpoint=env["apim_token_url"],
            token_validity_threshold=env["apim_token_expiry_threshold"].timedelta,
            session_manager=session_manager(),
        )

    return _apim_authenticator
