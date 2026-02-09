"""
Base class for FHIR API stubs.

Provides common functionality for creating stub responses.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from http.client import responses as http_responses
from typing import Any

from requests import Response
from requests.structures import CaseInsensitiveDict


class StubBase(ABC):
    """
    Abstract base class for FHIR API stubs.

    Provides common functionality for creating HTTP responses and defines
    the interface that all stub implementations must provide.
    """

    @staticmethod
    def _create_response(
        status_code: int,
        headers: dict[str, str],
        json_data: dict[str, Any],
    ) -> Response:
        """
        Create a :class:`requests.Response` object for the stub.

        :param status_code: HTTP status code.
        :param headers: Response headers dictionary.
        :param json_data: JSON body data.
        :return: A :class:`requests.Response` instance.
        """
        response = Response()
        response.status_code = status_code
        response.headers = CaseInsensitiveDict(headers)
        response._content = json.dumps(json_data).encode("utf-8")  # noqa: SLF001
        response.encoding = "utf-8"
        # Set a reason phrase for HTTP error handling
        response.reason = http_responses.get(status_code, "Unknown")
        return response

    @abstractmethod
    def get(
        self, url: str, headers: dict[str, str], params: dict[str, Any], timeout: int
    ) -> Response:
        """
        Handle HTTP GET requests for the stub.

        :param url: Request URL.
        :param headers: Request headers.
        :param params: Query parameters.
        :param timeout: Request timeout in seconds.
        :return: A :class:`requests.Response` instance.
        """

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

        :param url: Request URL.
        :param headers: Request headers.
        :param data: Request body data.
        :param timeout: Request timeout in seconds.
        :return: A :class:`requests.Response` instance.
        """
