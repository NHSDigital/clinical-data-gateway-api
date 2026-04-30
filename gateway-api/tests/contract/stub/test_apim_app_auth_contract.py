from unittest.mock import Mock

import pytest
import requests
from stubs.apim_app_auth.stub import APIMAppAuthStub


@pytest.fixture
def apim_app_auth_stub() -> APIMAppAuthStub:
    return APIMAppAuthStub()


@pytest.fixture
def mock_session() -> Mock:
    return Mock()


class TestAPIMAppAuthSuccess:
    def setup_method(self) -> None:
        self.mock_session = Mock()

    def test_post_success(
        self, apim_app_auth_stub: APIMAppAuthStub, mock_session: Mock
    ) -> None:
        mock_session.post.return_value.json.return_value = {
            "access_token": "access_token",
            "expires_in": "5",
        }
        mock_session.post.return_value.status_code = 200

        response = apim_app_auth_stub.session_post(
            requests.Session(),
            url="https://example.com/token",
            data="grant_type=client_credentials&client_id=abc&client_secret=def",
        )

        assert response.status_code == 200
        assert response.json() == {
            "access_token": "access_token",
            "expires_in": "5",
        }
