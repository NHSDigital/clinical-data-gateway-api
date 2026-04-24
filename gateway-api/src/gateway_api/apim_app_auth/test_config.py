import os
from datetime import timedelta
from typing import Any

import pytest

from gateway_api.apim_app_auth.config import (
    ConfigError,
    Duration,
    DurationUnit,
    get_environment_variable,
    get_optional_environment_variable,
)


class TestGetEnvironmentVariables:
    __ENV_VAR_NAME = "TEST_VARIABLE"

    def teardown_method(self) -> None:
        os.environ.pop(self.__ENV_VAR_NAME, None)

    @pytest.mark.parametrize(
        ("expected_value", "_type"),
        [
            pytest.param("test_value", str, id="String variable"),
            pytest.param(123, int, id="Integer variable"),
        ],
    )
    def test_get_environment_variable(
        self, expected_value: Any, _type: type[Any]
    ) -> None:
        os.environ[self.__ENV_VAR_NAME] = str(expected_value)

        value = get_environment_variable(name=self.__ENV_VAR_NAME, _type=_type)

        assert value == expected_value

    @pytest.mark.parametrize(
        ("_type"),
        [
            pytest.param(str, id="String variable"),
            pytest.param(int, id="Integer variable"),
        ],
    )
    def test_get_environment_variable_no_config_value(self, _type: type[Any]) -> None:
        with pytest.raises(
            ConfigError,
            match=f"Environment variable '{self.__ENV_VAR_NAME}' is not set",
        ):
            get_environment_variable(name=self.__ENV_VAR_NAME, _type=_type)

    @pytest.mark.parametrize(
        ("environment_variable", "expected_result"),
        [
            pytest.param(
                "5m",
                Duration(unit=DurationUnit.MINUTES, value=5),
                id="Minutes duration",
            ),
            pytest.param(
                "30s",
                Duration(unit=DurationUnit.SECONDS, value=30),
                id="Seconds duration",
            ),
        ],
    )
    def test_get_duration_environment_variable(
        self, environment_variable: str, expected_result: Duration
    ) -> None:
        os.environ[self.__ENV_VAR_NAME] = environment_variable

        value = get_environment_variable(name=self.__ENV_VAR_NAME, _type=Duration)

        assert value == expected_result

    @pytest.mark.parametrize(
        ("environment_variable", "expected_error"),
        [
            pytest.param(
                "5x",
                "Invalid duration value: '5x'",
                id="Unknown unit type",
            ),
            pytest.param(
                "invalids",
                "Invalid duration value: 'invalids'",
                id="Unknown unit",
            ),
            pytest.param(
                "not a duration",
                "Invalid duration value: 'not a duration'",
                id="Not a duration format",
            ),
            pytest.param(
                None,
                "Environment variable 'TEST_VARIABLE' is not set",
                id="No value",
            ),
        ],
    )
    def test_get_duration_environment_variable_invalid(
        self, environment_variable: str, expected_error: str
    ) -> None:
        if environment_variable is not None:
            os.environ[self.__ENV_VAR_NAME] = environment_variable

        with pytest.raises(ConfigError, match=expected_error):
            get_environment_variable(name=self.__ENV_VAR_NAME, _type=Duration)

    def test_get_environment_variable_unsupported_type(self) -> None:
        with pytest.raises(
            ValueError,
            match=f"Required type {float!r} is not supported for config values",
        ):
            get_environment_variable(name=self.__ENV_VAR_NAME, _type=float)

    @pytest.mark.parametrize(
        ("expected_value", "_type"),
        [
            pytest.param("test_value", str, id="String variable"),
            pytest.param(123, int, id="Integer variable"),
        ],
    )
    def test_get_optional_environment_variable(
        self, expected_value: Any, _type: type[Any]
    ) -> None:
        os.environ[self.__ENV_VAR_NAME] = str(expected_value)

        value = get_optional_environment_variable(name=self.__ENV_VAR_NAME, _type=_type)

        assert value == expected_value

    @pytest.mark.parametrize(
        ("_type"),
        [
            pytest.param(str, id="String variable"),
            pytest.param(int, id="Integer variable"),
            pytest.param(Duration, id="Duration variable"),
        ],
    )
    def test_get_optional_environment_variable_no_config_value(
        self, _type: type[Any]
    ) -> None:
        value = get_optional_environment_variable(name=self.__ENV_VAR_NAME, _type=_type)

        assert value is None

    @pytest.mark.parametrize(
        ("environment_variable", "expected_result"),
        [
            pytest.param(
                "5m",
                Duration(unit=DurationUnit.MINUTES, value=5),
                id="Minutes duration",
            ),
            pytest.param(
                "30s",
                Duration(unit=DurationUnit.SECONDS, value=30),
                id="Seconds duration",
            ),
        ],
    )
    def test_get_optional_duration_environment_variable(
        self, environment_variable: str, expected_result: Duration
    ) -> None:
        os.environ[self.__ENV_VAR_NAME] = environment_variable

        value = get_optional_environment_variable(
            name=self.__ENV_VAR_NAME, _type=Duration
        )

        assert value == expected_result

    @pytest.mark.parametrize(
        ("environment_variable", "expected_error"),
        [
            pytest.param(
                "5x",
                "Invalid duration value: '5x'",
                id="Unknown unit",
            ),
        ],
    )
    def test_get_optional_duration_environment_variable_invalid(
        self, environment_variable: str, expected_error: str
    ) -> None:
        os.environ[self.__ENV_VAR_NAME] = environment_variable

        with pytest.raises(ConfigError, match=expected_error):
            get_optional_environment_variable(name=self.__ENV_VAR_NAME, _type=Duration)

    def test_get_optional_environment_variable_unsupported_type(self) -> None:
        with pytest.raises(
            ValueError,
            match=f"Required type {float!r} is not supported for config values",
        ):
            get_optional_environment_variable(name=self.__ENV_VAR_NAME, _type=float)


class TestDuration:
    @pytest.mark.parametrize(
        ("duration", "expected_timedelta"),
        [
            pytest.param(
                Duration(unit=DurationUnit.MINUTES, value=5),
                timedelta(minutes=5),
                id="Minutes duration",
            ),
            pytest.param(
                Duration(unit=DurationUnit.SECONDS, value=30),
                timedelta(seconds=30),
                id="Seconds duration",
            ),
        ],
    )
    def test_timedelta(self, duration: Duration, expected_timedelta: timedelta) -> None:
        assert duration.timedelta == expected_timedelta
