import pytest

from gateway_api.handler import User, greet


class TestUser:
    """Test suite for the User class."""

    @pytest.mark.parametrize(
        "name",
        [
            "Alice",
            "Bob",
            "",
            "O'Brien",
        ],
    )
    def test_user_initialization(self, name: str) -> None:
        """Test that a User can be initialized with various names."""
        user = User(name)
        assert user.name == name

    def test_user_name_is_immutable(self) -> None:
        """Test that the name property cannot be directly modified."""
        user = User("Charlie")
        with pytest.raises(AttributeError):
            user.name = "David"  # type: ignore[misc]


class TestGreet:
    """Test suite for the greet function."""

    @pytest.mark.parametrize(
        ("name", "expected_greeting"),
        [
            ("Alice", "Hello, Alice!"),
            ("Bob", "Hello, Bob!"),
            ("", "Hello, !"),
            ("O'Brien", "Hello, O'Brien!"),
            ("Nonexistent", "Hello, Nonexistent!"),
            ("nonexistent ", "Hello, nonexistent !"),
        ],
    )
    def test_greet_with_valid_users(self, name: str, expected_greeting: str) -> None:
        """Test that greet returns the correct greeting for various valid users."""
        user = User(name)
        result = greet(user)
        assert result == expected_greeting

    def test_greet_with_nonexistent_user_raises_value_error(self) -> None:
        """Test that greet raises ValueError for nonexistent user."""
        user = User("nonexistent")
        with pytest.raises(ValueError, match="nonexistent user provided."):
            greet(user)
