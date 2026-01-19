# tests/test_controller.py
from types import SimpleNamespace
from typing import Any

import pytest
from requests import Response

from gateway_api.common.common import json_str
from gateway_api.controller import (
    Controller,
    SdsSearchResults,
    _coerce_nhs_number_to_int,
)
from gateway_api.pds_search import PdsSearchResults


class FakeResponse:
    def __init__(
        self, status_code: int, text: str, headers: dict[str, Any] | None = None
    ) -> None:
        self.status_code = status_code
        self.text = text
        self.headers = headers or {}


class FakePdsClient:
    last_init = None
    _patient_details = None

    def __init__(self, **kwargs: dict[str, Any]) -> None:
        # Controller constructs PdsClient with these kwargs
        FakePdsClient.last_init = kwargs
        self._result = kwargs.pop("_result", None)

    def set_patient_details(self, value: PdsSearchResults) -> None:
        self._patient_details = value

    def search_patient_by_nhs_number(
        self, nhs_number_int: int
    ) -> PdsSearchResults | None:
        # Patched per-test via class attribute
        return self._patient_details


class FakeSdsClient:
    _org_details = None

    def __init__(
        self,
        auth_token: str = "test_token",  # noqa S107 (fake test credentials)
        base_url: str = "test_url",
        timeout: int = 10,
    ) -> None:
        self.auth_token = auth_token
        self.base_url = base_url
        self.timeout = timeout

    def set_org_details(self, org_details: SdsSearchResults) -> None:
        self._org_details = org_details

    def get_org_details(self, ods_code: str) -> SdsSearchResults | None:
        return self._org_details


class FakeGpProviderClient:
    _status_code: int = 200
    _content: bytes = b"OK"

    def __init__(
        self, provider_endpoint: str, provider_asid: str, consumer_asid: str
    ) -> None:
        # Not actually using any of the constructor args for the stub
        pass

    def set_response_details(self, status_code: int, body_content: bytes) -> None:
        self._status_code = status_code
        self._content = body_content

    def access_structured_record(self, trace_id: str, body: json_str) -> Response:
        resp = Response()
        resp.status_code = self._status_code
        resp._content = self._content  # noqa SLF001 (Hacking internals for testing purposes)
        resp.headers["Content-Type"] = "text/plain; charset=utf-8"
        resp.url = "https://example.com/"
        resp.encoding = "utf-8"

        return resp


@pytest.fixture
def patched_deps(monkeypatch: pytest.MonkeyPatch) -> None:
    # Patch dependency classes in the controller module namespace.
    monkeypatch.setattr(Controller, "PdsClient", FakePdsClient)
    monkeypatch.setattr(Controller, "SdsClient", FakeSdsClient)
    monkeypatch.setattr(Controller, "GpConnectClient", FakeGpProviderClient)


def _make_controller() -> Controller:
    return Controller(
        pds_base_url="https://pds.example",
        sds_base_url="https://sds.example",
        nhsd_session_urid="session-123",
        timeout=3,
    )


def test__coerce_nhs_number_to_int_accepts_spaces_and_validates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Use real validator logic by default; 9434765919 is algorithmically valid.
    assert _coerce_nhs_number_to_int("943 476 5919") == 9434765919  # noqa SLF001 (testing)


@pytest.mark.parametrize("value", ["not-a-number", "943476591", "94347659190"])
def test__coerce_nhs_number_to_int_rejects_bad_inputs(value: Any) -> None:
    with pytest.raises(ValueError):  # noqa PT011 (Raises several different ValueErrors)
        _coerce_nhs_number_to_int(value)  # noqa SLF001 (testing)


def test__coerce_nhs_number_to_int_rejects_when_validator_returns_false(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(Controller, "validate_nhs_number", lambda _: False)
    with pytest.raises(ValueError, match="invalid"):
        _coerce_nhs_number_to_int("9434765919")  # noqa SLF001 (testing)


def test_call_gp_connect_returns_404_when_pds_patient_not_found(
    patched_deps: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(Controller, "_coerce_nhs_number_to_int", lambda _: 9434765919)

    c = _make_controller()

    # Configure FakePdsClient instance return value to None.
    def pds_init_side_effect(**kwargs: dict[str, Any]) -> FakePdsClient:
        inst = FakePdsClient(**kwargs)
        return inst

    monkeypatch.setattr(Controller, "PdsClient", pds_init_side_effect)

    r = c.call_gp_connect("9434765919", "token-abc")  # TODO: Create body and headers

    # TODO: Avoid one-letter variable names
    assert r.status_code == 404
    assert "No PDS patient found" in (r.data or "")


def test_call_gp_connect_returns_404_when_gp_ods_code_missing(
    patched_deps: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(Controller, "_coerce_nhs_number_to_int", lambda _: 9434765919)

    c = _make_controller()

    def pds_init_side_effect(**kwargs: dict[str, Any]) -> FakePdsClient:
        inst = FakePdsClient(**kwargs)
        inst.set_patient_details(SimpleNamespace(gp_ods_code="   "))
        return inst

    monkeypatch.setattr(Controller, "PdsClient", pds_init_side_effect)

    r = c.call_gp_connect(9434765919, "token-abc")  # TODO: Create body and headers
    assert r.status_code == 404
    assert "did not contain a current GP ODS code" in (r.data or "")


def test_call_gp_connect_returns_404_when_sds_returns_none(
    patched_deps: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(Controller, "_coerce_nhs_number_to_int", lambda _: 9434765919)

    c = _make_controller()

    def pds_init_side_effect(**kwargs: dict[str, Any]) -> FakePdsClient:
        inst = FakePdsClient(**kwargs)
        inst.set_patient_details(SimpleNamespace(gp_ods_code="A12345"))
        return inst

    def sds_init_side_effect(**kwargs: dict[str, Any]) -> FakeSdsClient:
        inst = FakeSdsClient(**kwargs)
        return inst

    monkeypatch.setattr(Controller, "PdsClient", pds_init_side_effect)
    monkeypatch.setattr(Controller, "SdsClient", sds_init_side_effect)

    r = c.call_gp_connect("9434765919", "token-abc")  # TODO: Create body and headers
    assert r.status_code == 404
    assert r.data == "No ASID found for ODS code A12345"


def test_call_gp_connect_returns_404_when_sds_asid_blank(
    patched_deps: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(Controller, "_coerce_nhs_number_to_int", lambda _: 9434765919)

    c = _make_controller()

    def pds_init_side_effect(**kwargs: dict[str, Any]) -> FakePdsClient:
        inst = FakePdsClient(**kwargs)
        inst.set_patient_details(
            SimpleNamespace(gp_ods_code="A12345")
        )  # TODO: Fix this for updated set_patient_details
        return inst

    def sds_init_side_effect(**kwargs: dict[str, Any]) -> FakeSdsClient:
        inst = FakeSdsClient(
            **kwargs
        )  # TODO: SDS args aren't this any more. Also check PDS.
        inst.set_asid_details(Controller.SdsSearchResults(asid="   "))
        return inst

    monkeypatch.setattr(Controller, "PdsClient", pds_init_side_effect)
    monkeypatch.setattr(Controller, "SdsClient", sds_init_side_effect)

    r = c.call_gp_connect("9434765919", "token-abc")  # TODO: Create body and headers
    assert r.status_code == 404
    assert "did not contain a current ASID" in (r.data or "")


def test_call_gp_connect_returns_502_when_gp_connect_returns_none(
    patched_deps: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(Controller, "_coerce_nhs_number_to_int", lambda _: 9434765919)

    c = _make_controller()

    def pds_init_side_effect(**kwargs: dict[str, Any]) -> FakePdsClient:
        inst = FakePdsClient(**kwargs)
        inst.set_patient_details(SimpleNamespace(gp_ods_code="A12345"))
        return inst

    def sds_init_side_effect(**kwargs: dict[str, Any]) -> FakeSdsClient:
        inst = FakeSdsClient(**kwargs)
        inst.set_asid_details(Controller.SdsSearchResults(asid="asid_A12345"))
        return inst

    monkeypatch.setattr(Controller, "PdsClient", pds_init_side_effect)
    monkeypatch.setattr(Controller, "SdsClient", sds_init_side_effect)

    r = c.call_gp_connect("9434765919", "token-abc")  # TODO: Create body and headers
    assert r.status_code == 502
    assert r.data == "GP Connect service error"
    assert r.headers is None


def test_call_gp_connect_happy_path_maps_status_text_headers_and_strips_asid(
    patched_deps: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(Controller, "_coerce_nhs_number_to_int", lambda _: 9434765919)

    c = _make_controller()

    def pds_init_side_effect(**kwargs: dict[str, Any]) -> FakePdsClient:
        inst = FakePdsClient(**kwargs)
        inst.set_patient_details(SimpleNamespace(gp_ods_code="  A12345  "))
        return inst

    def sds_init_side_effect(**kwargs: dict[str, Any]) -> FakeSdsClient:
        inst = FakeSdsClient(**kwargs)
        inst.set_asid_details(Controller.SdsSearchResults(asid="  asid_A12345  "))
        return inst

    c.gp_connect_client.access_structured_record(
        FakeResponse(
            status_code=200,
            text="ok",
            headers={"Content-Type": "application/fhir+json"},
        )
    )
    monkeypatch.setattr(Controller, "PdsClient", pds_init_side_effect)
    monkeypatch.setattr(Controller, "SdsClient", sds_init_side_effect)

    r = c.call_gp_connect("943 476 5919", "token-abc")
    assert r.status_code == 200
    assert r.data == "ok"
    assert r.headers == {"Content-Type": "application/fhir+json"}

    # Verify GP Connect called with coerced NHS number string and stripped ASID
    assert c.gp_connect_client.last_call == {
        "nhs_number": "9434765919",
        "asid": "asid_A12345",
        "auth_token": "token-abc",
    }


def test_call_gp_connect_constructs_pds_client_with_expected_kwargs(
    patched_deps: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(Controller, "_coerce_nhs_number_to_int", lambda _: 9434765919)

    c = _make_controller()

    def pds_init_side_effect(**kwargs: dict[str, Any]) -> FakePdsClient:
        inst = FakePdsClient(
            **kwargs
        )  # stop early (404) so we only assert constructor args
        return inst

    monkeypatch.setattr(Controller, "PdsClient", pds_init_side_effect)

    _ = c.call_gp_connect("9434765919", "token-abc")

    # These are the kwargs Controller passes into PdsClient()
    assert FakePdsClient.last_init["auth_token"] == "token-abc"  # noqa S105 (fake test credentials)
    assert FakePdsClient.last_init["end_user_org_ods"] == "ORG1"
    assert FakePdsClient.last_init["base_url"] == "https://pds.example"
    assert FakePdsClient.last_init["nhsd_session_urid"] == "session-123"
    assert FakePdsClient.last_init["timeout"] == 3
