import pytest
import requests
from pytest_bdd import scenarios

# Load all feature files from the 'features' directory
scenarios("features")


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
def context() -> ResponseContext:
    return ResponseContext()
