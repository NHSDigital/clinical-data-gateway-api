import pytest

from gateway_api.handler import User, greet


class TestUser:
    """Test suite for the User class."""

    def test_user_initialization(self) -> None:
        """Test that a User can be initialized with a name."""
        user = User("Alice")
        assert user.name == "Alice"

    def test_user_name_property(self) -> None:
        """Test that the name property returns the correct value."""
        user = User("Bob")
        assert user.name == "Bob"

    def test_user_with_empty_string(self) -> None:
        """Test that a User can be initialized with an empty string."""
        user = User("")
        assert user.name == ""

    def test_user_with_special_characters(self) -> None:
        """Test that a User can be initialized with special characters."""
        user = User("O'Brien")
        assert user.name == "O'Brien"

    def test_user_name_is_immutable(self) -> None:
        """Test that the name property cannot be directly modified."""
        user = User("Charlie")
        with pytest.raises(AttributeError):
            user.name = "David"  # type: ignore[misc]


class TestGreet:
    """Test suite for the greet function."""

    def test_greet_with_valid_user(self) -> None:
        """Test that greet returns the correct greeting for a valid user."""
        user = User("Alice")
        result = greet(user)
        assert result == "Hello, Alice!"

    def test_greet_with_different_user(self) -> None:
        """Test that greet returns the correct greeting for different users."""
        user = User("Bob")
        result = greet(user)
        assert result == "Hello, Bob!"

    def test_greet_with_empty_name(self) -> None:
        """Test that greet handles users with empty names."""
        user = User("")
        result = greet(user)
        assert result == "Hello, !"

    def test_greet_with_special_characters(self) -> None:
        """Test that greet handles users with special characters in their names."""
        user = User("O'Brien")
        result = greet(user)
        assert result == "Hello, O'Brien!"

    def test_greet_with_nonexistent_user_raises_value_error(self) -> None:
        """Test that greet raises ValueError for nonexistent user."""
        user = User("nonexistent")
        with pytest.raises(ValueError, match="nonexistent user provided."):
            greet(user)

    def test_greet_with_nonexistent_case_sensitive(self) -> None:
        """Test that the nonexistent check is case-sensitive."""
        user = User("Nonexistent")
        result = greet(user)
        assert result == "Hello, Nonexistent!"

    def test_greet_with_nonexistent_with_spaces(self) -> None:
        """Test that the nonexistent check is exact match only."""
        user = User("nonexistent ")
        result = greet(user)
        assert result == "Hello, nonexistent !"
