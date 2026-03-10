import datetime
import uuid

import pytest
from pydantic import BaseModel

from .elements import Identifier, Meta, UUIDIdentifier


class TestMeta:
    def test_create(self) -> None:
        meta = Meta(
            version_id="1",
            last_updated=datetime.datetime.fromisoformat("2023-10-01T12:00:00Z"),
        )
        assert meta.version_id == "1"
        assert meta.last_updated == datetime.datetime.fromisoformat(
            "2023-10-01T12:00:00Z"
        )

    def test_create_without_last_updated(self) -> None:
        meta = Meta(version_id="2")

        assert meta.version_id == "2"
        assert meta.last_updated is None

    def test_create_without_version(self) -> None:
        meta = Meta(
            last_updated=datetime.datetime.fromisoformat("2023-10-01T12:00:00Z")
        )

        assert meta.version_id is None
        assert meta.last_updated == datetime.datetime.fromisoformat(
            "2023-10-01T12:00:00Z"
        )

    def test_with_last_updated(self) -> None:
        last_updated = datetime.datetime.fromisoformat("2023-10-01T12:00:00Z")
        meta = Meta.with_last_updated(last_updated)

        assert meta.last_updated == last_updated
        assert meta.version_id is None

    def test_with_last_updated_defaults_to_now(self) -> None:
        before_create = datetime.datetime.now(tz=datetime.timezone.utc)
        meta = Meta.with_last_updated(None)
        after_create = datetime.datetime.now(tz=datetime.timezone.utc)

        assert meta.last_updated is not None
        assert meta.version_id is None

        assert before_create <= meta.last_updated
        assert meta.last_updated <= after_create


class TestUUIDIdentifier:
    def test_create_with_value(self) -> None:
        expected_uuid = uuid.UUID("12345678-1234-5678-1234-567812345678")
        identifier = UUIDIdentifier(value=expected_uuid)

        assert identifier.system == "https://tools.ietf.org/html/rfc4122"
        assert identifier.value == str(expected_uuid)

    def test_create_without_value(self) -> None:
        identifier = UUIDIdentifier()

        assert identifier.system == "https://tools.ietf.org/html/rfc4122"
        # Validates that value is a valid UUID v4
        parsed_uuid = uuid.UUID(identifier.value)
        assert parsed_uuid.version == 4


class TestIdentifier:
    def test_invalid_system(self) -> None:
        class _TestIdentifier(Identifier, expected_system="expected-system"):
            pass

        class _TestContainer(BaseModel):
            identifier: _TestIdentifier

        with pytest.raises(
            ValueError,
            match="Identifier system 'invalid-system' does not match expected "
            "system 'expected-system'.",
        ):
            _TestContainer.model_validate(
                {"identifier": {"system": "invalid-system", "value": "some-value"}}
            )
