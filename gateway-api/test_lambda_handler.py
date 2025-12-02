import pytest
from lambda_handler import handler


class TestHandler:
    """Unit tests for the Lambda handler function."""

    @pytest.mark.parametrize(
        ("name", "expected_greeting"),
        [
            ("Alice", "Hello, Alice!"),
            ("Bob", "Hello, Bob!"),
            ("John Doe", "Hello, John Doe!"),
            ("user123", "Hello, user123!"),
        ],
        ids=["simple_name_alice", "simple_name_bob", "name_with_space", "alphanumeric"],
    )
    def test_handler_success(self, name: str, expected_greeting: str) -> None:
        """Test handler returns 200 with greeting for valid names."""
        # Arrange
        event = {"payload": name}
        context: dict[str, str] = {}

        # Act
        response = handler(event, context)

        # Assert
        assert response["statusCode"] == 200
        assert response["body"] == expected_greeting
        assert response["headers"] == {"Content-Type": "application/json"}

    @pytest.mark.parametrize(
        ("event", "expected_status", "expected_body"),
        [
            ({"other_key": "value"}, 400, "Name is required"),
            ({"payload": ""}, 400, "Name cannot be empty"),
            ({"payload": None}, 400, "Name cannot be empty"),
            (
                {"payload": "nonexistent"},
                404,
                "Provided name cannot be found. name=nonexistent",
            ),
        ],
        ids=[
            "missing_payload_key",
            "empty_payload",
            "none_payload",
            "nonexistent_user",
        ],
    )
    def test_handler_error_cases(
        self, event: dict[str, str], expected_status: int, expected_body: str
    ) -> None:
        """Test handler returns appropriate error responses for invalid or
        nonexistent input.
        """
        # Act
        response = handler(event, {})

        # Assert
        assert response["statusCode"] == expected_status
        assert response["body"] == expected_body
        assert response["headers"] == {"Content-Type": "application/json"}
