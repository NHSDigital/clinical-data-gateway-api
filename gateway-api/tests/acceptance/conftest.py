import pytest
import requests


class ResponseContext:
    _response: requests.Response | None = None

    @property
    def response(self) -> requests.Response | None:
        return self._response

    @response.setter
    def response(self, value: requests.Response) -> None:
        if self._response:
            raise RuntimeError("Response has already been set.")
        self._response = value


@pytest.fixture
def response_context() -> ResponseContext:
    return ResponseContext()
