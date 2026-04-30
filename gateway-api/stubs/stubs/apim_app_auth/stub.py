"""
In-memory APIM APP Auth API stub.

The stub does **not** implement the full APIM APP Auth API surface.
"""

import logging
from typing import Any

from requests import Response, Session

from stubs.base_stub import SessionPostStub, StubBase


class APIMAppAuthStub(StubBase, SessionPostStub):
    def __init__(self) -> None:
        self._post_url: str = ""
        self._post_headers: dict[str, str] = {}
        self._post_data: str | dict[str, str] = {}
        self._post_timeout: int | None = None
        self._post_session: Session = Session()

    @property
    def post_url(self) -> str:
        return self._post_url

    @property
    def post_headers(self) -> dict[str, str]:
        return self._post_headers

    @property
    def post_data(self) -> str | dict[str, str]:
        return self._post_data

    @property
    def post_timeout(self) -> int | None:
        return self._post_timeout

    @property
    def post_session(self) -> Session:
        return self._post_session

    def post(
        self,
        url: str,
        data: str,
        **kwargs: Any,
    ) -> Response:
        return self.session_post(
            session=kwargs.pop("session", Session()),
            url=url,
            data=data,
            **kwargs,
        )

    def session_post(
        self,
        session: Session,
        url: str,  # noqa: ARG002 - required to match subclass signature
        data: str | dict[str, str],  # noqa: ARG002 - required to match subclass signature
        **kwargs: Any,  # noqa: ARG002 - required to match subclass signature
    ) -> Response:
        logger = logging.getLogger(__name__)
        logger.info("DaveW in stub session_post data: %s", data)
        if session is None:
            raise ValueError("Session must be provided for APIMAppAuthStub")

        # contract test flag on env var e.g. api_token

        # session_post_response = session.post(url, data=data, **kwargs)

        # if session_post_response.text == "Unauthorized":
        #     response = self._create_response(
        #         status_code=401, json_data={"error": "Unauthorized"}
        #     )
        # else:
        response = self._create_response(
            status_code=200,
            json_data={
                "access_token": "access_token",
                "expires_in": "5",
            },
        )

        return response
