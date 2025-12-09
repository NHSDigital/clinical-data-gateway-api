from clinical_data_common import get_hello  # type: ignore[import-untyped]


class User:
    def __init__(self, name: str):
        self._name = name

    @property
    def name(self) -> str:
        return self._name


def greet(user: User) -> str:
    if user.name == "nonexistent":
        raise ValueError("nonexistent user provided.")
    hello = get_hello()
    return f"{hello}{user.name}!"
