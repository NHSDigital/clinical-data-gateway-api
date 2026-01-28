"""
Unit tests for :mod:`gateway_api.controller`.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

import pytest
from flask import Flask
from flask import request as flask_request
from requests import Response

import gateway_api.controller as controller_module
from gateway_api.controller import (
    Controller,
    SdsSearchResults,
)
from gateway_api.get_structured_record.request import GetStructuredRecordRequest

if TYPE_CHECKING:
    from gateway_api.common.common import json_str


# -----------------------------
# Helpers for request test data
# -----------------------------
# def make_request_body(nhs_number: str = "9434765919") -> json_str:
#     """
#     Legacy helper (previous controller signature) retained for backwards compatibility
#     with older tests. New tests use GetStructuredRecordRequest fixture.
#     """
#     return std_json.dumps({"nhs-number": nhs_number})


# TODO: Remove this and the one above
# def make_headers(
#     ods_from: str = "ORG1",
#     trace_id: str = "trace-123",
# ) -> dict[str, str]:
#     """
#     Legacy helper (previous controller signature) retained for backwards compatibility
#     with older tests. New tests use GetStructuredRecordRequest fixture.
#     """
#     return {"Ods-from": ods_from, "X-Request-ID": trace_id}


# -----------------------------
# Fake downstream dependencies
# -----------------------------
def _make_pds_result(gp_ods_code: str | None) -> Any:
    """
    Construct a minimal PDS-result-like object for tests.

    The controller only relies on the ``gp_ods_code`` attribute.

    :param gp_ods_code: Provider ODS code to expose on the result.
    :returns: An object with a ``gp_ods_code`` attribute.
    """
    return SimpleNamespace(gp_ods_code=gp_ods_code)


class FakePdsClient:
    """
    Test double for :class:`gateway_api.pds_search.PdsClient`.

    The controller instantiates this class and calls ``search_patient_by_nhs_number``.
    Tests configure the returned patient details using ``set_patient_details``.
    """

    last_init: dict[str, Any] | None = None

    def __init__(self, **kwargs: Any) -> None:
        FakePdsClient.last_init = dict(kwargs)
        self._patient_details: Any | None = None

    def set_patient_details(self, value: Any) -> None:
        self._patient_details = value

    def search_patient_by_nhs_number(self, nhs_number: int) -> Any | None:
        return self._patient_details


class FakeSdsClient:
    """
    Test double for :class:`gateway_api.controller.SdsClient`.

    Tests configure per-ODS results using ``set_org_details`` and the controller
    retrieves them via ``get_org_details``.
    """

    last_init: dict[str, Any] | None = None

    def __init__(
        self,
        auth_token: str | None = None,
        base_url: str = "test_url",
        timeout: int = 10,
    ) -> None:
        FakeSdsClient.last_init = {
            "auth_token": auth_token,
            "base_url": base_url,
            "timeout": timeout,
        }
        self.auth_token = auth_token
        self.base_url = base_url
        self.timeout = timeout
        self._org_details_by_ods: dict[str, SdsSearchResults | None] = {}

    def set_org_details(
        self, ods_code: str, org_details: SdsSearchResults | None
    ) -> None:
        self._org_details_by_ods[ods_code] = org_details

    def get_org_details(self, ods_code: str) -> SdsSearchResults | None:
        return self._org_details_by_ods.get(ods_code)


class FakeGpProviderClient:
    """
    Test double for :class:`gateway_api.controller.GpProviderClient`.

    The controller instantiates this class and calls ``access_structured_record``.
    Tests configure the returned HTTP response using class-level attributes.
    """

    last_init: dict[str, str] | None = None
    last_call: dict[str, str] | None = None

    # Configure per-test.
    return_none: bool = False
    response_status_code: int = 200
    response_body: bytes = b"ok"
    response_headers: dict[str, str] = {"Content-Type": "application/fhir+json"}

    def __init__(
        self, provider_endpoint: str, provider_asid: str, consumer_asid: str
    ) -> None:
        FakeGpProviderClient.last_init = {
            "provider_endpoint": provider_endpoint,
            "provider_asid": provider_asid,
            "consumer_asid": consumer_asid,
        }

    def access_structured_record(
        self,
        trace_id: str,
        body: json_str,
    ) -> Response | None:
        FakeGpProviderClient.last_call = {"trace_id": trace_id, "body": body}

        if FakeGpProviderClient.return_none:
            return None

        resp = Response()
        resp.status_code = FakeGpProviderClient.response_status_code
        resp._content = FakeGpProviderClient.response_body  # noqa: SLF001
        resp.encoding = "utf-8"
        resp.headers.update(FakeGpProviderClient.response_headers)
        resp.url = "https://example.invalid/fake"
        return resp


@dataclass
class SdsSetup:
    """
    Helper dataclass to hold SDS setup data for tests.
    """

    ods_code: str
    search_results: SdsSearchResults


class sds_factory:
    """
    Factory to create a :class:`FakeSdsClient` pre-configured with up to two
    organisations.
    """

    def __init__(
        self,
        org1: SdsSetup | None = None,
        org2: SdsSetup | None = None,
    ) -> None:
        self.org1 = org1
        self.org2 = org2

    def __call__(self, **kwargs: Any) -> FakeSdsClient:
        self.inst = FakeSdsClient(**kwargs)
        if self.org1 is not None:
            self.inst.set_org_details(
                self.org1.ods_code,
                SdsSearchResults(
                    asid=self.org1.search_results.asid,
                    endpoint=self.org1.search_results.endpoint,
                ),
            )

        if self.org2 is not None:
            self.inst.set_org_details(
                self.org2.ods_code,
                SdsSearchResults(
                    asid=self.org2.search_results.asid,
                    endpoint=self.org2.search_results.endpoint,
                ),
            )
        return self.inst


class pds_factory:
    """
    Factory to create a :class:`FakePdsClient` pre-configured with patient details.
    """

    def __init__(self, ods_code: str | None) -> None:
        self.ods_code = ods_code

    def __call__(self, **kwargs: Any) -> FakePdsClient:
        self.inst = FakePdsClient(**kwargs)
        self.inst.set_patient_details(_make_pds_result(self.ods_code))
        return self.inst


@pytest.fixture
def patched_deps(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Patch controller dependencies to use test fakes.
    """
    monkeypatch.setattr(controller_module, "PdsClient", FakePdsClient)
    monkeypatch.setattr(controller_module, "SdsClient", FakeSdsClient)
    monkeypatch.setattr(controller_module, "GpProviderClient", FakeGpProviderClient)


@pytest.fixture
def controller() -> Controller:
    """
    Construct a controller instance configured for unit tests.
    """
    return Controller(
        pds_base_url="https://pds.example",
        sds_base_url="https://sds.example",
        nhsd_session_urid="session-123",
        timeout=3,
    )


@pytest.fixture
def get_structured_record_request(
    request: pytest.FixtureRequest,
) -> GetStructuredRecordRequest:
    app = Flask(__name__)

    # Pass two dicts to this fixture that give dicts to add to
    # header and body respectively.
    header_update, body_update = request.param

    headers = {
        "Ssp-TraceID": "3d7f2a6e-0f4e-4af3-9b7b-2a3d5f6a7b8c",
        "ODS-from": "CONSUMER",
    }

    headers.update(header_update)

    body = {
        "resourceType": "Parameters",
        "parameter": [
            {
                "valueIdentifier": {
                    "system": "https://fhir.nhs.uk/Id/nhs-number",
                    "value": "9999999999",
                },
            }
        ],
    }

    body.update(body_update)

    with app.test_request_context(
        path="/patient/$gpc.getstructuredrecord",
        method="POST",
        headers=headers,
        json=body,
    ):
        return GetStructuredRecordRequest(flask_request)


# -----------------------------
# Unit tests
# -----------------------------


@pytest.mark.parametrize(
    "get_structured_record_request",
    [({}, {})],
    indirect=["get_structured_record_request"],
)
def test_call_gp_provider_returns_200_on_success(
    patched_deps: Any,
    monkeypatch: pytest.MonkeyPatch,
    controller: Controller,
    get_structured_record_request: GetStructuredRecordRequest,
) -> None:
    """
    On successful end-to-end call, the controller should return 200 with
    expected body/headers.
    """
    pds = pds_factory(ods_code="PROVIDER")
    sds_org1 = SdsSetup(
        ods_code="PROVIDER",
        search_results=SdsSearchResults(
            asid="asid_PROV", endpoint="https://provider.example/ep"
        ),
    )
    sds_org2 = SdsSetup(
        ods_code="CONSUMER",
        search_results=SdsSearchResults(asid="asid_CONS", endpoint=None),
    )
    sds = sds_factory(org1=sds_org1, org2=sds_org2)

    monkeypatch.setattr(controller_module, "PdsClient", pds)
    monkeypatch.setattr(controller_module, "SdsClient", sds)

    FakeGpProviderClient.response_status_code = 200
    FakeGpProviderClient.response_body = b'{"resourceType":"Bundle"}'
    FakeGpProviderClient.response_headers = {
        "Content-Type": "application/fhir+json",
        "X-Downstream": "gp-provider",
    }

    r = controller.run(get_structured_record_request)

    # Check that response from GP provider was passed through.
    assert r.status_code == 200
    assert r.data == FakeGpProviderClient.response_body.decode("utf-8")
    assert r.headers == FakeGpProviderClient.response_headers

    # Check that GP provider was initialised correctly
    assert FakeGpProviderClient.last_init == {
        "provider_endpoint": "https://provider.example/ep",
        "provider_asid": "asid_PROV",
        "consumer_asid": "asid_CONS",
    }

    # Check that we passed the trace ID and body to the provider
    assert FakeGpProviderClient.last_call == {
        "trace_id": get_structured_record_request.trace_id,
        "body": get_structured_record_request.request_body,
    }


@pytest.mark.parametrize(
    "get_structured_record_request",
    [({}, {})],
    indirect=["get_structured_record_request"],
)
def test_call_gp_provider_returns_404_when_pds_patient_not_found(
    patched_deps: Any,
    controller: Controller,
    get_structured_record_request: GetStructuredRecordRequest,
) -> None:
    """
    If PDS returns no patient record, the controller should return 404.
    """
    # FakePdsClient defaults to returning None => RequestError => 404
    r = controller.run(get_structured_record_request)

    assert r.status_code == 404
    assert "No PDS patient found for NHS number" in (r.data or "")


@pytest.mark.parametrize(
    "get_structured_record_request",
    [({}, {})],
    indirect=["get_structured_record_request"],
)
def test_call_gp_provider_returns_404_when_gp_ods_code_missing(
    patched_deps: Any,
    monkeypatch: pytest.MonkeyPatch,
    controller: Controller,
    get_structured_record_request: GetStructuredRecordRequest,
) -> None:
    """
    If PDS returns a patient without a provider (GP) ODS code, return 404.
    """
    pds = pds_factory(ods_code="")
    monkeypatch.setattr(controller_module, "PdsClient", pds)

    r = controller.run(get_structured_record_request)

    assert r.status_code == 404
    assert "did not contain a current provider ODS code" in (r.data or "")


@pytest.mark.parametrize(
    "get_structured_record_request",
    [({}, {})],
    indirect=["get_structured_record_request"],
)
def test_call_gp_provider_returns_404_when_sds_returns_none_for_provider(
    patched_deps: Any,
    monkeypatch: pytest.MonkeyPatch,
    controller: Controller,
    get_structured_record_request: GetStructuredRecordRequest,
) -> None:
    """
    If SDS returns no provider org details, the controller should return 404.
    """
    pds = pds_factory(ods_code="PROVIDER")
    sds = sds_factory()

    monkeypatch.setattr(controller_module, "PdsClient", pds)
    monkeypatch.setattr(controller_module, "SdsClient", sds)

    r = controller.run(get_structured_record_request)

    assert r.status_code == 404
    assert r.data == "No SDS org found for provider ODS code PROVIDER"


@pytest.mark.parametrize(
    "get_structured_record_request",
    [({}, {})],
    indirect=["get_structured_record_request"],
)
def test_call_gp_provider_returns_404_when_sds_provider_asid_blank(
    patched_deps: Any,
    monkeypatch: pytest.MonkeyPatch,
    controller: Controller,
    get_structured_record_request: GetStructuredRecordRequest,
) -> None:
    """
    If provider ASID is blank/whitespace, the controller should return 404.
    """
    pds = pds_factory(ods_code="PROVIDER")
    sds_org1 = SdsSetup(
        ods_code="PROVIDER",
        search_results=SdsSearchResults(
            asid="   ", endpoint="https://provider.example/ep"
        ),
    )
    sds = sds_factory(org1=sds_org1)

    monkeypatch.setattr(controller_module, "PdsClient", pds)
    monkeypatch.setattr(controller_module, "SdsClient", sds)

    r = controller.run(get_structured_record_request)

    assert r.status_code == 404
    assert "did not contain a current ASID" in (r.data or "")


@pytest.mark.parametrize(
    "get_structured_record_request",
    [({"ODS-from": "CONSUMER"}, {})],
    indirect=["get_structured_record_request"],
)
def test_call_gp_provider_returns_502_when_gp_provider_returns_none(
    patched_deps: Any,
    monkeypatch: pytest.MonkeyPatch,
    controller: Controller,
    get_structured_record_request: GetStructuredRecordRequest,
) -> None:
    """
    If GP provider returns no response object, the controller should return 502.
    """
    pds = pds_factory(ods_code="PROVIDER")
    sds_org1 = SdsSetup(
        ods_code="PROVIDER",
        search_results=SdsSearchResults(
            asid="asid_PROV", endpoint="https://provider.example/ep"
        ),
    )
    sds_org2 = SdsSetup(
        ods_code="CONSUMER",
        search_results=SdsSearchResults(asid="asid_CONS", endpoint=None),
    )
    sds = sds_factory(org1=sds_org1, org2=sds_org2)

    monkeypatch.setattr(controller_module, "PdsClient", pds)
    monkeypatch.setattr(controller_module, "SdsClient", sds)

    FakeGpProviderClient.return_none = True

    r = controller.run(get_structured_record_request)

    assert r.status_code == 502
    assert r.data == "GP provider service error"
    assert r.headers is None

    # reset for other tests
    # TODO: Do we need this? Really?
    FakeGpProviderClient.return_none = False


@pytest.mark.parametrize(
    "get_structured_record_request",
    [({"ODS-from": "CONSUMER"}, {})],
    indirect=["get_structured_record_request"],
)
def test_call_gp_provider_constructs_pds_client_with_expected_kwargs(
    patched_deps: Any,
    monkeypatch: pytest.MonkeyPatch,
    controller: Controller,
    get_structured_record_request: GetStructuredRecordRequest,
) -> None:
    """
    Validate that the controller constructs the PDS client with expected kwargs.
    """
    _ = controller.run(get_structured_record_request)  # will stop at PDS None => 404

    assert FakePdsClient.last_init is not None
    assert FakePdsClient.last_init["auth_token"] == "PLACEHOLDER_AUTH_TOKEN"  # noqa: S105
    assert FakePdsClient.last_init["end_user_org_ods"] == "CONSUMER"
    assert FakePdsClient.last_init["base_url"] == "https://pds.example"
    assert FakePdsClient.last_init["nhsd_session_urid"] == "session-123"
    assert FakePdsClient.last_init["timeout"] == 3


@pytest.mark.parametrize(
    "get_structured_record_request",
    [({}, {"parameter": [{"valueIdentifier": {"value": "1234567890"}}]})],
    indirect=["get_structured_record_request"],
)
def test_call_gp_provider_404_message_includes_nhs_number_from_request_body(
    patched_deps: Any,
    controller: Controller,
    get_structured_record_request: GetStructuredRecordRequest,
) -> None:
    """
    If PDS returns no patient record, error message should include NHS number parsed
    from the FHIR Parameters request body.
    """
    r = controller.run(get_structured_record_request)

    assert r.status_code == 404
    assert r.data == "No PDS patient found for NHS number 1234567890"


@pytest.mark.parametrize(
    "get_structured_record_request",
    [({"ODS-from": ""}, {})],
    indirect=["get_structured_record_request"],
)
def test_call_gp_provider_returns_400_when_ods_from_is_empty(
    patched_deps: Any,
    controller: Controller,
    get_structured_record_request: GetStructuredRecordRequest,
) -> None:
    """
    If the required ``ODS-from`` header is empty/falsy, return 400.
    """
    r = controller.run(get_structured_record_request)

    assert r.status_code == 400
    assert r.data == 'Missing required header "Ods-from"'


@pytest.mark.parametrize(
    "get_structured_record_request",
    [({"Ssp-TraceID": ""}, {})],
    indirect=["get_structured_record_request"],
)
def test_call_gp_provider_passes_empty_trace_id_through_to_gp_provider(
    patched_deps: Any,
    monkeypatch: pytest.MonkeyPatch,
    controller: Controller,
    get_structured_record_request: GetStructuredRecordRequest,
) -> None:
    """
    If Ssp-TraceID is present but empty, we get a 400
    """
    pds = pds_factory(ods_code="PROVIDER")
    sds_org1 = SdsSetup(
        ods_code="PROVIDER",
        search_results=SdsSearchResults(
            asid="asid_PROV", endpoint="https://provider.example/ep"
        ),
    )
    sds_org2 = SdsSetup(
        ods_code="CONSUMER",
        search_results=SdsSearchResults(asid="asid_CONS", endpoint=None),
    )
    sds = sds_factory(org1=sds_org1, org2=sds_org2)

    monkeypatch.setattr(controller_module, "PdsClient", pds)
    monkeypatch.setattr(controller_module, "SdsClient", sds)

    r = controller.run(get_structured_record_request)

    assert r.status_code == 400
    assert "Missing required header: Ssp-TraceID" in (r.data or "")


@pytest.mark.parametrize(
    "get_structured_record_request",
    [({"ODS-from": "CONSUMER"}, {})],
    indirect=["get_structured_record_request"],
)
def test_call_gp_provider_returns_404_when_sds_provider_endpoint_blank(
    patched_deps: Any,
    monkeypatch: pytest.MonkeyPatch,
    controller: Controller,
    get_structured_record_request: GetStructuredRecordRequest,
) -> None:
    """
    If provider endpoint is blank/whitespace, the controller should return 404.
    """
    pds = pds_factory(ods_code="PROVIDER")
    sds_org1 = SdsSetup(
        ods_code="PROVIDER",
        search_results=SdsSearchResults(asid="asid_PROV", endpoint="   "),
    )
    sds = sds_factory(org1=sds_org1)

    monkeypatch.setattr(controller_module, "PdsClient", pds)
    monkeypatch.setattr(controller_module, "SdsClient", sds)

    r = controller.run(get_structured_record_request)

    assert r.status_code == 404
    assert "did not contain a current endpoint" in (r.data or "")


@pytest.mark.parametrize(
    "get_structured_record_request",
    [({"ODS-from": "CONSUMER"}, {})],
    indirect=["get_structured_record_request"],
)
def test_call_gp_provider_returns_404_when_sds_returns_none_for_consumer(
    patched_deps: Any,
    monkeypatch: pytest.MonkeyPatch,
    controller: Controller,
    get_structured_record_request: GetStructuredRecordRequest,
) -> None:
    """
    If SDS returns no consumer org details, the controller should return 404.
    """
    pds = pds_factory(ods_code="PROVIDER")
    sds_org1 = SdsSetup(
        ods_code="PROVIDER",
        search_results=SdsSearchResults(
            asid="asid_PROV", endpoint="https://provider.example/ep"
        ),
    )
    sds = sds_factory(org1=sds_org1)

    monkeypatch.setattr(controller_module, "PdsClient", pds)
    monkeypatch.setattr(controller_module, "SdsClient", sds)

    r = controller.run(get_structured_record_request)

    assert r.status_code == 404
    assert r.data == "No SDS org found for consumer ODS code CONSUMER"


@pytest.mark.parametrize(
    "get_structured_record_request",
    [({"ODS-from": "CONSUMER"}, {})],
    indirect=["get_structured_record_request"],
)
def test_call_gp_provider_returns_404_when_sds_consumer_asid_blank(
    patched_deps: Any,
    monkeypatch: pytest.MonkeyPatch,
    controller: Controller,
    get_structured_record_request: GetStructuredRecordRequest,
) -> None:
    """
    If consumer ASID is blank/whitespace, the controller should return 404.
    """
    pds = pds_factory(ods_code="PROVIDER")
    sds_org1 = SdsSetup(
        ods_code="PROVIDER",
        search_results=SdsSearchResults(
            asid="asid_PROV", endpoint="https://provider.example/ep"
        ),
    )
    sds_org2 = SdsSetup(
        ods_code="CONSUMER",
        search_results=SdsSearchResults(asid="   ", endpoint=None),
    )
    sds = sds_factory(org1=sds_org1, org2=sds_org2)

    monkeypatch.setattr(controller_module, "PdsClient", pds)
    monkeypatch.setattr(controller_module, "SdsClient", sds)

    r = controller.run(get_structured_record_request)

    assert r.status_code == 404
    assert "did not contain a current ASID" in (r.data or "")


@pytest.mark.parametrize(
    "get_structured_record_request",
    [({"ODS-from": "CONSUMER"}, {})],
    indirect=["get_structured_record_request"],
)
def test_call_gp_provider_passthroughs_non_200_gp_provider_response(
    patched_deps: Any,
    monkeypatch: pytest.MonkeyPatch,
    controller: Controller,
    get_structured_record_request: GetStructuredRecordRequest,
) -> None:
    """
    Validate that non-200 responses from GP provider are passed through.
    """
    pds = pds_factory(ods_code="PROVIDER")
    sds_org1 = SdsSetup(
        ods_code="PROVIDER",
        search_results=SdsSearchResults(
            asid="asid_PROV", endpoint="https://provider.example/ep"
        ),
    )
    sds_org2 = SdsSetup(
        ods_code="CONSUMER",
        search_results=SdsSearchResults(asid="asid_CONS", endpoint=None),
    )
    sds = sds_factory(org1=sds_org1, org2=sds_org2)

    monkeypatch.setattr(controller_module, "PdsClient", pds)
    monkeypatch.setattr(controller_module, "SdsClient", sds)

    FakeGpProviderClient.response_status_code = 404
    FakeGpProviderClient.response_body = b"Not Found"
    FakeGpProviderClient.response_headers = {
        "Content-Type": "text/plain",
        "X-Downstream": "gp-provider",
    }

    r = controller.run(get_structured_record_request)

    assert r.status_code == 404
    assert r.data == "Not Found"
    assert r.headers is not None
    assert r.headers.get("Content-Type") == "text/plain"
    assert r.headers.get("X-Downstream") == "gp-provider"
