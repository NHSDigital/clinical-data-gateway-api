# tests/test_controller.py
from types import SimpleNamespace

import pytest
from src.gateway_api.controller import controller


class FakeResponse:
    def __init__(self, status_code: int, text: str, headers=None):
        self.status_code = status_code
        self.text = text
        self.headers = headers or {}


class FakePdsClient:
    last_init = None
    _patient_details = None

    def __init__(self, **kwargs):
        # Controller constructs PdsClient with these kwargs
        FakePdsClient.last_init = kwargs
        self._result = kwargs.pop("_result", None)

    def set_patient_details(self, value):
        self._patient_details = value

    def search_patient_by_nhs_number(self, nhs_number_int: int):
        # Patched per-test via class attribute
        return self._patient_details


class FakeSdsClient:
    _asid_details = None

    def __init__(self, auth_token=None, base_url=None, timeout=10):
        self.auth_token = auth_token
        self.base_url = base_url
        self.timeout = timeout

    def set_asid_details(self, value):
        self._asid_details = value

    def get_asid(self, ods_code: str):
        return self._asid_details


class FakeGpConnectClient:
    _patient_records = None

    def __init__(self, base_url=None, timeout=10):
        self.base_url = base_url
        self.timeout = timeout
        self.last_call = None

    def set_patient_records(self, value):
        self._patient_records = value

    def get_patient_records(self, nhs_number: str, asid: str, auth_token: str):
        self.last_call = {
            "nhs_number": nhs_number,
            "asid": asid,
            "auth_token": auth_token,
        }
        return self._patient_records


@pytest.fixture
def patched_deps(monkeypatch):
    # Patch dependency classes in the controller module namespace.
    monkeypatch.setattr(controller, "PdsClient", FakePdsClient)
    monkeypatch.setattr(controller, "SdsClient", FakeSdsClient)
    monkeypatch.setattr(controller, "GpConnectClient", FakeGpConnectClient)


def _make_controller():
    return controller.Controller(
        pds_end_user_org_ods="ORG1",
        pds_base_url="https://pds.example",
        nhsd_session_urid="session-123",
        timeout=3,
        sds_base_url="https://sds.example",
        gp_connect_base_url="https://gp.example",
    )


def test__coerce_nhs_number_to_int_accepts_spaces_and_validates(monkeypatch):
    # Use real validator logic by default; 9434765919 is algorithmically valid.
    assert controller._coerce_nhs_number_to_int("943 476 5919") == 9434765919  # noqa SLF001 (testing)


@pytest.mark.parametrize("value", ["not-a-number", "943476591", "94347659190"])
def test__coerce_nhs_number_to_int_rejects_bad_inputs(value):
    with pytest.raises(ValueError):  # noqa PT011 (Raises several different ValueErrors)
        controller._coerce_nhs_number_to_int(value)  # noqa SLF001 (testing)


def test__coerce_nhs_number_to_int_rejects_when_validator_returns_false(monkeypatch):
    monkeypatch.setattr(controller, "validate_nhs_number", lambda _: False)
    with pytest.raises(ValueError, match="invalid"):
        controller._coerce_nhs_number_to_int("9434765919")  # noqa SLF001 (testing)


def test_call_gp_connect_returns_404_when_pds_patient_not_found(
    patched_deps, monkeypatch
):
    monkeypatch.setattr(controller, "_coerce_nhs_number_to_int", lambda _: 9434765919)

    c = _make_controller()

    # Configure FakePdsClient instance return value to None.
    def pds_init_side_effect(**kwargs):
        inst = FakePdsClient(**kwargs)
        return inst

    monkeypatch.setattr(controller, "PdsClient", pds_init_side_effect)

    r = c.call_gp_connect("9434765919", "token-abc")
    assert r.status_code == 404
    assert "No PDS patient found" in (r.data or "")


def test_call_gp_connect_returns_404_when_gp_ods_code_missing(
    patched_deps, monkeypatch
):
    monkeypatch.setattr(controller, "_coerce_nhs_number_to_int", lambda _: 9434765919)

    c = _make_controller()

    def pds_init_side_effect(**kwargs):
        inst = FakePdsClient(**kwargs)
        inst.set_patient_details(SimpleNamespace(gp_ods_code="   "))
        return inst

    monkeypatch.setattr(controller, "PdsClient", pds_init_side_effect)

    r = c.call_gp_connect(9434765919, "token-abc")
    assert r.status_code == 404
    assert "did not contain a current GP ODS code" in (r.data or "")


def test_call_gp_connect_returns_404_when_sds_returns_none(patched_deps, monkeypatch):
    monkeypatch.setattr(controller, "_coerce_nhs_number_to_int", lambda _: 9434765919)

    c = _make_controller()

    def pds_init_side_effect(**kwargs):
        inst = FakePdsClient(**kwargs)
        inst.set_patient_details(SimpleNamespace(gp_ods_code="A12345"))
        return inst

    def sds_init_side_effect(**kwargs):
        inst = FakeSdsClient(**kwargs)
        return inst

    monkeypatch.setattr(controller, "PdsClient", pds_init_side_effect)
    monkeypatch.setattr(controller, "SdsClient", sds_init_side_effect)

    r = c.call_gp_connect("9434765919", "token-abc")
    assert r.status_code == 404
    assert r.data == "No ASID found for ODS code A12345"


def test_call_gp_connect_returns_404_when_sds_asid_blank(patched_deps, monkeypatch):
    monkeypatch.setattr(controller, "_coerce_nhs_number_to_int", lambda _: 9434765919)

    c = _make_controller()

    def pds_init_side_effect(**kwargs):
        inst = FakePdsClient(**kwargs)
        inst.set_patient_details(SimpleNamespace(gp_ods_code="A12345"))
        return inst

    def sds_init_side_effect(**kwargs):
        inst = FakeSdsClient(**kwargs)
        inst.set_asid_details(controller.SdsSearchResults(asid="   "))
        return inst

    monkeypatch.setattr(controller, "PdsClient", pds_init_side_effect)
    monkeypatch.setattr(controller, "SdsClient", sds_init_side_effect)

    r = c.call_gp_connect("9434765919", "token-abc")
    assert r.status_code == 404
    assert "did not contain a current ASID" in (r.data or "")


def test_call_gp_connect_returns_502_when_gp_connect_returns_none(
    patched_deps, monkeypatch
):
    monkeypatch.setattr(controller, "_coerce_nhs_number_to_int", lambda _: 9434765919)

    c = _make_controller()

    def pds_init_side_effect(**kwargs):
        inst = FakePdsClient(**kwargs)
        inst.set_patient_details(SimpleNamespace(gp_ods_code="A12345"))
        return inst

    def sds_init_side_effect(**kwargs):
        inst = FakeSdsClient(**kwargs)
        inst.set_asid_details(controller.SdsSearchResults(asid="asid_A12345"))
        return inst

    monkeypatch.setattr(controller, "PdsClient", pds_init_side_effect)
    monkeypatch.setattr(controller, "SdsClient", sds_init_side_effect)

    r = c.call_gp_connect("9434765919", "token-abc")
    assert r.status_code == 502
    assert r.data == "GP Connect service error"
    assert r.headers is None


def test_call_gp_connect_happy_path_maps_status_text_headers_and_strips_asid(
    patched_deps, monkeypatch
):
    monkeypatch.setattr(controller, "_coerce_nhs_number_to_int", lambda _: 9434765919)

    c = _make_controller()

    def pds_init_side_effect(**kwargs):
        inst = FakePdsClient(**kwargs)
        inst.set_patient_details(SimpleNamespace(gp_ods_code="  A12345  "))
        return inst

    def sds_init_side_effect(**kwargs):
        inst = FakeSdsClient(**kwargs)
        inst.set_asid_details(controller.SdsSearchResults(asid="  asid_A12345  "))
        return inst

    c.gp_connect_client.set_patient_records(
        FakeResponse(
            status_code=200,
            text="ok",
            headers={"Content-Type": "application/fhir+json"},
        )
    )
    monkeypatch.setattr(controller, "PdsClient", pds_init_side_effect)
    monkeypatch.setattr(controller, "SdsClient", sds_init_side_effect)

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
    patched_deps, monkeypatch
):
    monkeypatch.setattr(controller, "_coerce_nhs_number_to_int", lambda _: 9434765919)

    c = _make_controller()

    def pds_init_side_effect(**kwargs):
        inst = FakePdsClient(
            **kwargs
        )  # stop early (404) so we only assert constructor args
        return inst

    monkeypatch.setattr(controller, "PdsClient", pds_init_side_effect)

    _ = c.call_gp_connect("9434765919", "token-abc")

    # These are the kwargs Controller passes into PdsClient()
    assert FakePdsClient.last_init["auth_token"] == "token-abc"  # noqa S105 (fake test credentials)
    assert FakePdsClient.last_init["end_user_org_ods"] == "ORG1"
    assert FakePdsClient.last_init["base_url"] == "https://pds.example"
    assert FakePdsClient.last_init["nhsd_session_urid"] == "session-123"
    assert FakePdsClient.last_init["timeout"] == 3
