import functools
import logging
import tempfile
from collections.abc import Callable
from contextlib import ExitStack
from datetime import timedelta
from typing import Any, Concatenate, TypedDict

import requests
from requests.adapters import HTTPAdapter

from gateway_api.apim_app_auth.request_context import get_correlation_id

_logger = logging.getLogger(__name__)

# Type alias describing the expected signature for a request making a HTTP request.
# Any function that takes a `requests.Session` as its first argument, followed by any
# number of additional arguments, and returns any type of value.
type RequestMethod[**P, S] = Callable[Concatenate[requests.Session, P], S]


class ClientCertificate(TypedDict):
    certificate: str
    key: str


class SessionManager:
    class _Adapter(HTTPAdapter):
        """
        HTTPAdapter to apply default configuration to apply to all created
        `request.Session` objects.
        """

        def __init__(self, timeout: float):
            self._timeout = timeout
            super().__init__()

        def send(
            self,
            request: requests.PreparedRequest,
            *args: Any,
            **kwargs: Any,
        ) -> requests.Response:
            kwargs["timeout"] = self._timeout
            if "X-Correlation-ID" not in request.headers:
                request.headers["X-Correlation-ID"] = get_correlation_id().short_id

            _logger.info(
                "Sending HTTP request. method=%s url=%s headers=%s",
                request.method,
                request.url,
                # Omit Authorization header from logging
                {
                    k: v
                    for k, v in request.headers.items()
                    if k.lower() != "authorization"
                },
            )
            response = super().send(request, *args, **kwargs)
            _logger.info(
                "Received HTTP response. status_code=%s response_headers=%s",
                response.status_code,
                response.headers,
            )

            return response

    def __init__(
        self,
        client_timeout: timedelta,
        client_certificate: ClientCertificate | None = None,
    ):
        self._client_adapter = self._Adapter(timeout=client_timeout.total_seconds())
        self._client_certificate = client_certificate

    def with_session[**P, S](self, func: RequestMethod[P, S]) -> Callable[P, S]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with ExitStack() as stack:
                session = requests.Session()
                stack.enter_context(session)

                session.mount("https://", self._client_adapter)

                if self._client_certificate is not None:
                    # File added to Exit stack and will be automatically cleaned up with
                    # the stack.
                    cert_file = tempfile.NamedTemporaryFile(  # noqa: SIM115
                        delete=True
                    )
                    stack.enter_context(cert_file)

                    # File added to Exit stack and will be automatically cleaned up with
                    # the stack.
                    key_file = tempfile.NamedTemporaryFile(  # noqa: SIM115
                        delete=True
                    )
                    stack.enter_context(key_file)

                    cert_file.write(self._client_certificate["certificate"].encode())
                    cert_file.flush()
                    key_file.write(self._client_certificate["key"].encode())
                    key_file.flush()

                    session.cert = (cert_file.name, key_file.name)

                return func(session, *args, **kwargs)

        return wrapper
