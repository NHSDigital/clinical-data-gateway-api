"""Get Structured Record module."""

from gateway_api.get_structured_record.request import (
    ACCESS_RECORD_STRUCTURED_INTERACTION_ID,
    GetStructuredRecordRequest,
    RequestValidationError,
)

__all__ = [
    "RequestValidationError",
    "GetStructuredRecordRequest",
    "ACCESS_RECORD_STRUCTURED_INTERACTION_ID",
]
