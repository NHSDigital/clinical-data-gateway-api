# tests/test_controller.py
from __future__ import annotations

import json as std_json
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

import pytest
from requests import Response

import gateway_api.controller as controller_module
from gateway_api.controller import (
    Controller,
    SdsSearchResults,
    _coerce_nhs_number_to_int,
)

if TYPE_CHECKING:
    from gateway_api.common.common import json_str


# -----------------------------
# Helpers for request test data
# -----------------------------
def make_request_body(nhs_number: str = "9434765919") -> json_str:
    # Controller expects a JSON string containing an "nhs-number" field.
    return std_json.dumps({"nhs-number": nhs_number})


def make_headers(
    ods_from: str = "ORG1",
    trace_id: str = "trace-123",
) -> dict[str, str]:
    # Controller expects these headers:
    # - Ods-from (consumer ODS)
    # - X-Request-ID (trace id)
    return {"Ods-from": ods_from, "X-Request-ID": trace_id}


# -----------------------------
# Fake downstream dependencies
# -----------------------------
def _make_pds_result(gp_ods_code: str | None) -> Any:
    # We only need .gp_ods_code for controller logic.
    return SimpleNamespace(gp_ods_code=gp_ods_code)


class FakePdsClient:
    last_init: dict[str, Any] | None = None

    def __init__(self, **kwargs: Any) -> None:
        # Controller constructs PdsClient with kwargs; capture for assertions.
        FakePdsClient.last_init = dict(kwargs)
        self._patient_details: Any | None = None

    def set_patient_details(self, value: Any) -> None:
        # Keep call sites explicit and "correct": pass a PDS-result-like object.
        self._patient_details = value

    def search_patient_by_nhs_number(self, nhs_number: int) -> Any | None:
        return self._patient_details


class FakeSdsClient:
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


class FakeGpConnectClient:
    last_init: dict[str, str] | None = None
    last_call: dict[str, str] | None = None

    # Configure per-test
    return_none: bool = False
    response_status_code: int = 200
    response_body: bytes = b"ok"
    response_headers: dict[str, str] = {"Content-Type": "application/fhir+json"}

    def __init__(
        self, provider_endpoint: str, provider_asid: str, consumer_asid: str
    ) -> None:
        FakeGpConnectClient.last_init = {
            "provider_endpoint": provider_endpoint,
            "provider_asid": provider_asid,
            "consumer_asid": consumer_asid,
        }

    def access_structured_record(
        self,
        trace_id: str,
        body: json_str,
        nhsnumber: str,
    ) -> Response | None:
        FakeGpConnectClient.last_call = {
            "trace_id": trace_id,
            "body": body,
            "nhsnumber": nhsnumber,
        }

        if FakeGpConnectClient.return_none:
            return None

        resp = Response()
        resp.status_code = FakeGpConnectClient.response_status_code
        resp._content = FakeGpConnectClient.response_body  # noqa: SLF001
        resp.encoding = "utf-8"
        resp.headers.update(FakeGpConnectClient.response_headers)
        resp.url = "https://example.invalid/fake"
        return resp


@pytest.fixture
def patched_deps(monkeypatch: pytest.MonkeyPatch) -> None:
    # Patch dependency classes in the *module* namespace that Controller uses.
    monkeypatch.setattr(controller_module, "PdsClient", FakePdsClient)
    monkeypatch.setattr(controller_module, "SdsClient", FakeSdsClient)
    monkeypatch.setattr(controller_module, "GpConnectClient", FakeGpConnectClient)


def _make_controller() -> Controller:
    return Controller(
        pds_base_url="https://pds.example",
        sds_base_url="https://sds.example",
        nhsd_session_urid="session-123",
        timeout=3,
    )


# -----------------------------
# Unit tests
# -----------------------------
def test__coerce_nhs_number_to_int_accepts_spaces_and_validates() -> None:
    # Use real validator logic by default; 9434765919 is algorithmically valid.
    assert _coerce_nhs_number_to_int("943 476 5919") == 9434765919  # noqa: SLF001 (testing private member)


@pytest.mark.parametrize("value", ["not-a-number", "943476591", "94347659190"])
def test__coerce_nhs_number_to_int_rejects_bad_inputs(value: Any) -> None:
    with pytest.raises(ValueError):  # noqa: PT011 (ValueError is correct here)
        _coerce_nhs_number_to_int(value)  # noqa: SLF001 (testing private member)


def test__coerce_nhs_number_to_int_rejects_when_validator_returns_false(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # _coerce_nhs_number_to_int calls validate_nhs_number imported into
    # gateway_api.controller
    monkeypatch.setattr(controller_module, "validate_nhs_number", lambda _: False)
    with pytest.raises(ValueError, match="invalid"):
        _coerce_nhs_number_to_int("9434765919")  # noqa: SLF001 (testing private member)


def test_call_gp_connect_returns_404_when_pds_patient_not_found(
    patched_deps: Any,
) -> None:
    c = _make_controller()

    # PDS returns None by default
    body = make_request_body("9434765919")
    headers = make_headers()

    r = c.call_gp_connect(body, headers, "token-abc")

    assert r.status_code == 404
    assert "No PDS patient found for NHS number" in (r.data or "")


def test_call_gp_connect_returns_404_when_gp_ods_code_missing(
    patched_deps: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    c = _make_controller()

    def pds_factory(**kwargs: Any) -> FakePdsClient:
        inst = FakePdsClient(**kwargs)
        # missing gp_ods_code should be a PDS error
        inst.set_patient_details(_make_pds_result(""))
        return inst

    monkeypatch.setattr(controller_module, "PdsClient", pds_factory)

    body = make_request_body("9434765919")
    headers = make_headers()

    r = c.call_gp_connect(body, headers, "token-abc")

    assert r.status_code == 404
    assert "did not contain a current provider ODS code" in (r.data or "")


def test_call_gp_connect_returns_404_when_sds_returns_none_for_provider(
    patched_deps: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    c = _make_controller()

    def pds_factory(**kwargs: Any) -> FakePdsClient:
        inst = FakePdsClient(**kwargs)
        inst.set_patient_details(_make_pds_result("A12345"))
        return inst

    def sds_factory(**kwargs: Any) -> FakeSdsClient:
        inst = FakeSdsClient(**kwargs)
        # Do NOT set provider org details => None
        return inst

    monkeypatch.setattr(controller_module, "PdsClient", pds_factory)
    monkeypatch.setattr(controller_module, "SdsClient", sds_factory)

    body = make_request_body("9434765919")
    headers = make_headers()

    r = c.call_gp_connect(body, headers, "token-abc")

    assert r.status_code == 404
    assert r.data == "No SDS org found for provider ODS code A12345"


def test_call_gp_connect_returns_404_when_sds_provider_asid_blank(
    patched_deps: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    c = _make_controller()

    def pds_factory(**kwargs: Any) -> FakePdsClient:
        inst = FakePdsClient(**kwargs)
        inst.set_patient_details(_make_pds_result("A12345"))
        return inst

    def sds_factory(**kwargs: Any) -> FakeSdsClient:
        inst = FakeSdsClient(**kwargs)
        inst.set_org_details(
            "A12345",
            SdsSearchResults(asid="   ", endpoint="https://provider.example/ep"),
        )
        return inst

    monkeypatch.setattr(controller_module, "PdsClient", pds_factory)
    monkeypatch.setattr(controller_module, "SdsClient", sds_factory)

    body = make_request_body("9434765919")
    headers = make_headers()

    r = c.call_gp_connect(body, headers, "token-abc")

    assert r.status_code == 404
    assert "did not contain a current ASID" in (r.data or "")


def test_call_gp_connect_returns_502_when_gp_connect_returns_none(
    patched_deps: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    GPConnectClient only returns None if we didn't call/get a response from
    GP Connect, in which case 502 is correct
    """
    c = _make_controller()

    def pds_factory(**kwargs: Any) -> FakePdsClient:
        inst = FakePdsClient(**kwargs)
        inst.set_patient_details(_make_pds_result("A12345"))
        return inst

    def sds_factory(**kwargs: Any) -> FakeSdsClient:
        inst = FakeSdsClient(**kwargs)
        inst.set_org_details(
            "A12345",
            SdsSearchResults(
                asid="asid_A12345", endpoint="https://provider.example/ep"
            ),
        )
        inst.set_org_details("ORG1", SdsSearchResults(asid="asid_ORG1", endpoint=None))
        return inst

    monkeypatch.setattr(controller_module, "PdsClient", pds_factory)
    monkeypatch.setattr(controller_module, "SdsClient", sds_factory)

    FakeGpConnectClient.return_none = True

    body = make_request_body("9434765919")
    headers = make_headers()

    r = c.call_gp_connect(body, headers, "token-abc")

    assert r.status_code == 502
    assert r.data == "GP Connect service error"
    assert r.headers is None

    # reset for other tests
    FakeGpConnectClient.return_none = False


def test_call_gp_connect_constructs_pds_client_with_expected_kwargs(
    patched_deps: Any,
) -> None:
    c = _make_controller()

    body = make_request_body("9434765919")
    headers = make_headers(ods_from="ORG1", trace_id="trace-123")

    _ = c.call_gp_connect(body, headers, "token-abc")  # will stop at PDS None => 404

    assert FakePdsClient.last_init is not None
    assert FakePdsClient.last_init["auth_token"] == "token-abc"  # noqa: S105
    assert FakePdsClient.last_init["end_user_org_ods"] == "ORG1"
    assert FakePdsClient.last_init["base_url"] == "https://pds.example"
    assert FakePdsClient.last_init["nhsd_session_urid"] == "session-123"
    assert FakePdsClient.last_init["timeout"] == 3


def test_call_gp_connect_returns_400_when_request_body_not_valid_json(
    patched_deps: Any,
) -> None:
    c = _make_controller()
    headers = make_headers()

    r = c.call_gp_connect("{", headers, "token-abc")

    assert r.status_code == 400
    assert r.data == 'Request body must be valid JSON with an "nhs-number" field'


def test_call_gp_connect_returns_400_when_request_body_is_not_an_object(
    patched_deps: Any,
) -> None:
    c = _make_controller()
    headers = make_headers()

    r = c.call_gp_connect('["9434765919"]', headers, "token-abc")

    assert r.status_code == 400
    assert r.data == 'Request body must be a JSON object with an "nhs-number" field'


def test_call_gp_connect_returns_400_when_request_body_missing_nhs_number(
    patched_deps: Any,
) -> None:
    c = _make_controller()
    headers = make_headers()

    r = c.call_gp_connect("{}", headers, "token-abc")

    assert r.status_code == 400
    assert r.data == 'Missing required field "nhs-number" in JSON request body'


def test_call_gp_connect_returns_400_when_nhs_number_not_coercible(
    patched_deps: Any,
) -> None:
    c = _make_controller()
    headers = make_headers()

    r = c.call_gp_connect(std_json.dumps({"nhs-number": "ABC"}), headers, "token-abc")

    assert r.status_code == 400
    assert r.data == 'Could not coerce NHS number "ABC" to an integer'


def test_call_gp_connect_returns_400_when_missing_ods_from_header(
    patched_deps: Any,
) -> None:
    c = _make_controller()
    body = make_request_body("9434765919")

    r = c.call_gp_connect(body, {"X-Request-ID": "trace-123"}, "token-abc")

    assert r.status_code == 400
    assert r.data == 'Missing required header "Ods-from"'


def test_call_gp_connect_returns_400_when_ods_from_is_whitespace(
    patched_deps: Any,
) -> None:
    c = _make_controller()
    body = make_request_body("9434765919")

    r = c.call_gp_connect(
        body, {"Ods-from": "   ", "X-Request-ID": "trace-123"}, "token-abc"
    )

    assert r.status_code == 400
    assert r.data == 'Missing required header "Ods-from"'


def test_call_gp_connect_returns_400_when_missing_x_request_id(
    patched_deps: Any,
) -> None:
    c = _make_controller()
    body = make_request_body("9434765919")

    r = c.call_gp_connect(body, {"Ods-from": "ORG1"}, "token-abc")

    assert r.status_code == 400
    assert r.data == "Missing required header: X-Request-ID"


def test_call_gp_connect_returns_404_when_sds_provider_endpoint_blank(
    patched_deps: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    c = _make_controller()

    def pds_factory(**kwargs: Any) -> FakePdsClient:
        inst = FakePdsClient(**kwargs)
        inst.set_patient_details(_make_pds_result("A12345"))
        return inst

    def sds_factory(**kwargs: Any) -> FakeSdsClient:
        inst = FakeSdsClient(**kwargs)
        inst.set_org_details(
            "A12345", SdsSearchResults(asid="asid_A12345", endpoint="   ")
        )
        inst.set_org_details("ORG1", SdsSearchResults(asid="asid_ORG1", endpoint=None))
        return inst

    monkeypatch.setattr(controller_module, "PdsClient", pds_factory)
    monkeypatch.setattr(controller_module, "SdsClient", sds_factory)

    r = c.call_gp_connect(make_request_body("9434765919"), make_headers(), "token-abc")

    assert r.status_code == 404
    assert "did not contain a current endpoint" in (r.data or "")


def test_call_gp_connect_returns_404_when_sds_returns_none_for_consumer(
    patched_deps: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    c = _make_controller()

    def pds_factory(**kwargs: Any) -> FakePdsClient:
        inst = FakePdsClient(**kwargs)
        inst.set_patient_details(_make_pds_result("A12345"))
        return inst

    def sds_factory(**kwargs: Any) -> FakeSdsClient:
        inst = FakeSdsClient(**kwargs)
        inst.set_org_details(
            "A12345",
            SdsSearchResults(
                asid="asid_A12345", endpoint="https://provider.example/ep"
            ),
        )
        # No consumer org details
        return inst

    monkeypatch.setattr(controller_module, "PdsClient", pds_factory)
    monkeypatch.setattr(controller_module, "SdsClient", sds_factory)

    r = c.call_gp_connect(
        make_request_body("9434765919"), make_headers(ods_from="ORG1"), "token-abc"
    )

    assert r.status_code == 404
    assert r.data == "No SDS org found for consumer ODS code ORG1"


def test_call_gp_connect_returns_404_when_sds_consumer_asid_blank(
    patched_deps: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    c = _make_controller()

    def pds_factory(**kwargs: Any) -> FakePdsClient:
        inst = FakePdsClient(**kwargs)
        inst.set_patient_details(_make_pds_result("A12345"))
        return inst

    def sds_factory(**kwargs: Any) -> FakeSdsClient:
        inst = FakeSdsClient(**kwargs)
        inst.set_org_details(
            "A12345",
            SdsSearchResults(
                asid="asid_A12345", endpoint="https://provider.example/ep"
            ),
        )
        inst.set_org_details("ORG1", SdsSearchResults(asid="   ", endpoint=None))
        return inst

    monkeypatch.setattr(controller_module, "PdsClient", pds_factory)
    monkeypatch.setattr(controller_module, "SdsClient", sds_factory)

    r = c.call_gp_connect(
        make_request_body("9434765919"), make_headers(ods_from="ORG1"), "token-abc"
    )

    assert r.status_code == 404
    assert "did not contain a current ASID" in (r.data or "")


def test_call_gp_connect_passthroughs_non_200_gp_connect_response(
    patched_deps: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    c = _make_controller()

    def pds_factory(**kwargs: Any) -> FakePdsClient:
        inst = FakePdsClient(**kwargs)
        inst.set_patient_details(_make_pds_result("A12345"))
        return inst

    def sds_factory(**kwargs: Any) -> FakeSdsClient:
        inst = FakeSdsClient(**kwargs)
        inst.set_org_details(
            "A12345",
            SdsSearchResults(
                asid="asid_A12345", endpoint="https://provider.example/ep"
            ),
        )
        inst.set_org_details("ORG1", SdsSearchResults(asid="asid_ORG1", endpoint=None))
        return inst

    monkeypatch.setattr(controller_module, "PdsClient", pds_factory)
    monkeypatch.setattr(controller_module, "SdsClient", sds_factory)

    FakeGpConnectClient.response_status_code = 404
    FakeGpConnectClient.response_body = b"Not Found"
    FakeGpConnectClient.response_headers = {
        "Content-Type": "text/plain",
        "X-Downstream": "gp-connect",
    }

    r = c.call_gp_connect(make_request_body("9434765919"), make_headers(), "token-abc")

    assert r.status_code == 404
    assert r.data == "Not Found"
    assert r.headers is not None
    assert r.headers.get("Content-Type") == "text/plain"
    assert r.headers.get("X-Downstream") == "gp-connect"
