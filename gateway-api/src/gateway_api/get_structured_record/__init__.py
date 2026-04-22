"""Get Structured Record module."""

from gateway_api.get_structured_record.request import (
    ACCESS_RECORD_STRUCTURED_INTERACTION_ID,
    SDS_SANDBOX_INTERACTION_ID,
    GetStructuredRecordRequest,
)
from gateway_api.get_structured_record.response import GetStructuredRecordResponse

__all__ = [
    "GetStructuredRecordRequest",
    "GetStructuredRecordResponse",
    "ACCESS_RECORD_STRUCTURED_INTERACTION_ID",
    "SDS_SANDBOX_INTERACTION_ID",
]
