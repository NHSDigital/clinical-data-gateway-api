import pytest

from apim.get_auth_token import get_app_credentials, get_key_id


class TestGetAuthToken:
    @pytest.mark.parametrize(
        ("args", "expected_api_key", "expected_path", "expected_env"),
        [
            (
                ["test_api_key", "/path/to/test_key.pem", "--env", "test-env"],
                "test_api_key",
                "/path/to/test_key.pem",
                "test-env",
            ),
            (
                ["another_key", ".keys/another_key.pem", "--env", "production"],
                "another_key",
                ".keys/another_key.pem",
                "production",
            ),
            (
                ["default_key", ".keys/default.pem"],
                "default_key",
                ".keys/default.pem",
                "internal-dev",
            ),
            (
                ["key123", "/full/path/to/key.pem", "--env", "staging"],
                "key123",
                "/full/path/to/key.pem",
                "staging",
            ),
        ],
    )
    def test_get_app_credentials(
        self, args, expected_api_key, expected_path, expected_env
    ):
        api_key, path_to_private_key, env = get_app_credentials(args)

        assert api_key == expected_api_key
        assert path_to_private_key == expected_path
        assert env == expected_env

    @pytest.mark.parametrize(
        ("path", "expected_key_id"),
        [
            ("/some/path/to/key_456.pem", "key_456"),
            (".keys/my-api-key.pem", "my-api-key"),
            ("relative/path/test_key.pem", "test_key"),
            ("/absolute/nested/path/production-key.pem", "production-key"),
            ("simple.pem", "simple"),
            (".keys/key-with-dashes.pem", "key-with-dashes"),
        ],
    )
    def test_get_key_id(self, path, expected_key_id):
        key_id = get_key_id(path)

        assert key_id == expected_key_id
