import os
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum
from typing import Any, cast


class ConfigError(Exception):
    pass


class DurationUnit(StrEnum):
    SECONDS = "s"
    MINUTES = "m"


@dataclass(frozen=True)
class Duration:
    unit: DurationUnit
    value: int

    @property
    def timedelta(self) -> timedelta:
        match self.unit:
            case DurationUnit.SECONDS:
                return timedelta(seconds=self.value)
            case DurationUnit.MINUTES:
                return timedelta(minutes=self.value)


_SUPPORTED_PRIMITIVES: dict[type[Any], Callable[[str], Any]] = {
    str: str,
    int: int,
}


def get_optional_environment_variable[T](name: str, _type: type[T]) -> T | None:
    value = os.getenv(name)

    match _type:
        case _ if _type is Duration:
            if value is None:
                return None

            parsed = re.fullmatch(r"(?P<value>\d+)(?P<unit>[sm])", value)
            if parsed is None:
                raise ConfigError(f"Invalid duration value: {value!r}")

            raw_value = parsed.group("value")
            raw_unit = parsed.group("unit")

            return cast(
                "T",
                Duration(
                    unit=DurationUnit(raw_unit),
                    value=int(raw_value),
                ),
            )

        case _ if _type in _SUPPORTED_PRIMITIVES:
            if value is None:
                return None

            return cast("T", _SUPPORTED_PRIMITIVES[_type](value))

        case _:
            raise ValueError(
                f"Required type {_type} is not supported for config values"
            )


def get_environment_variable[T](name: str, _type: type[T]) -> T:
    value = get_optional_environment_variable(name=name, _type=_type)
    if value is None:
        raise ConfigError(f"Environment variable {name!r} is not set")
    return value
