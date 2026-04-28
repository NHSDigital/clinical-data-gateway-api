"""
In-memory APIM APP Auth API stub.

The stub does **not** implement the full APIM APP Auth API surface.
"""

from typing import Any

from requests import Response

from stubs.base_stub import PostStub, StubBase


class APIMAppAuthStub(StubBase, PostStub):
    def __init__(self) -> None:
        self._post_url: str = ""
        self._post_headers: dict[str, str] = {}
        self._post_data: str = ""
        self._post_timeout: int | None = None

    @property
    def post_url(self) -> str:
        return self._post_url

    @property
    def post_headers(self) -> dict[str, str]:
        return self._post_headers

    @property
    def post_data(self) -> str:
        return self._post_data

    @property
    def post_timeout(self) -> int | None:
        return self._post_timeout

    # TODO: validation?

    def post(
        self,
        url: str,
        data: str,
        **kwargs: Any,  # noqa: ARG002 - kwargs are required to match subclass signature
    ) -> Response:
        self._post_url = url
        self._post_data = data

        response = self._create_response(
            status_code=200,
            json_data={
                "access_token": "access_token",
                "expires_in": "599",
                "token_type": "Bearer",
                "issued_at": "1777366854223",
            },
        )

        return response
