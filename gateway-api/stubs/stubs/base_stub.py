"""
Base class for FHIR API stubs.

Provides common functionality for creating stub responses.
"""

from __future__ import annotations

import json
from abc import abstractmethod
from http.client import responses as http_responses
from typing import Any, Protocol

from requests import Response
from requests.structures import CaseInsensitiveDict


class StubBase:
    """
    Base class for FHIR API stubs.

    Provides common functionality for creating HTTP responses and defines
    the interface that all stub implementations must provide.

    Recommended to subclass with GetStub or PostStub (or both)
    """

    @staticmethod
    def _create_response(
        status_code: int,
        headers: dict[str, str],
        json_data: dict[str, Any],
    ) -> Response:
        """
        Create a :class:`requests.Response` object for the stub.
        """
        response = Response()
        response.status_code = status_code
        response.headers = CaseInsensitiveDict(headers)
        response._content = json.dumps(json_data).encode("utf-8")  # noqa: SLF001 to customise stub
        response.encoding = "utf-8"
        # Set a reason phrase for HTTP error handling
        response.reason = http_responses.get(status_code, "Unknown")
        return response


class GetStub(Protocol):
    @abstractmethod
    def get(
        self, url: str, headers: dict[str, str], params: dict[str, Any], timeout: int
    ) -> Response:
        """
        Handle HTTP GET requests for the stub.
        """

    @property
    @abstractmethod
    def get_url(self) -> str:
        """
        Last URL stub.get was called with. Empty string if not called yet.
        """

    @property
    @abstractmethod
    def get_headers(self) -> dict[str, str]:
        """
        Dict of last headers stub.get was called with. Empty if not called yet.
        """

    @property
    @abstractmethod
    def get_params(self) -> dict[str, str]:
        """
        Dict of last get parameters stub.get was called with. Empty if not called yet.
        """

    @property
    @abstractmethod
    def get_timeout(self) -> int | None:
        """
        Last timeout value stub.get was called with. None if not called yet.
        """


class PostStub(Protocol):
    @abstractmethod
    def post(
        self,
        url: str,
        headers: dict[str, Any],
        data: str,
        timeout: int,
    ) -> Response:
        """
        Handle HTTP POST requests for the stub.
        """

    @property
    @abstractmethod
    def post_url(self) -> str:
        """
        Last URL stub.post was called with. Empty string if not called yet.
        """

    @property
    @abstractmethod
    def post_headers(self) -> dict[str, str]:
        """
        Dict of last headers stub.post was called with. Empty if not called yet.
        """

    @property
    @abstractmethod
    def post_data(self) -> str:
        """
        Last post request body stub.gpostet was called with. Empty if not called yet.
        """

    @property
    @abstractmethod
    def post_timeout(self) -> int | None:
        """
        Last timeout value stub.post was called with. None if not called yet.
        """
