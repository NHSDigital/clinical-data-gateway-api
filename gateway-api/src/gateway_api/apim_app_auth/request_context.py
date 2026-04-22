from contextvars import ContextVar
from typing import NamedTuple


class CorrelationID(NamedTuple):
    full_id: str
    short_id: str


_correlation_id: ContextVar[CorrelationID | None] = ContextVar(
    "correlation_id", default=None
)


def set_correlation_id(full_id: str, short_id: str) -> None:
    """Set the correlation ID for the current request context."""
    _correlation_id.set(CorrelationID(full_id=full_id, short_id=short_id))


def reset_correlation_id() -> None:
    """Reset the correlation ID to the default empty string."""
    _correlation_id.set(None)


def get_correlation_id() -> CorrelationID:
    """Get the correlation ID for the current request context."""
    if (correlation_id := _correlation_id.get()) is None:
        raise ValueError("Correlation ID is not set in the current context.")
    return correlation_id
