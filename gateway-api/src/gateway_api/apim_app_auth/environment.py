# TODO: 395 update this to align with the new environment
# variable management approach once that is implemented

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
    apim_private_key_name: str
    apim_api_key_name: str
    apim_token_expiry_threshold: Duration
    apim_key_id: str
    pdm_url: str
    mns_url: str


_environment: Environment | None = None
_session_manager: SessionManager | None = None
_apim_authenticator: ApimAuthenticator | None = None


def values() -> Environment:
    global _environment
    if _environment is None:
        _environment = Environment(
            client_timeout=get_environment_variable(
                "CLIENT_TIMEOUT",
                Duration,
            ),
            apim_token_url=get_environment_variable(
                "APIM_TOKEN_URL",
                str,
            ),
            apim_private_key_name=get_environment_variable(
                "APIM_PRIVATE_KEY_NAME",
                str,
            ),
            apim_api_key_name=get_environment_variable(
                "APIM_API_KEY_NAME",
                str,
            ),
            apim_token_expiry_threshold=get_environment_variable(
                "APIM_TOKEN_EXPIRY_THRESHOLD",
                Duration,
            ),
            apim_key_id=get_environment_variable(
                "APIM_KEY_ID",
                str,
            ),
            pdm_url=get_environment_variable(
                "PDM_BUNDLE_URL",
                str,
            ),
            mns_url=get_environment_variable(
                "MNS_EVENT_URL",
                str,
            ),
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
            private_key="",  # TODO: 395 get private key
            key_id=env["apim_key_id"],
            api_key="",  # TODO: 395 get api key
            token_endpoint=env["apim_token_url"],
            token_validity_threshold=env["apim_token_expiry_threshold"].timedelta,
            session_manager=session_manager(),
        )

    return _apim_authenticator
