"""
Unit tests for :mod:`gateway_api.controller`.
"""

from __future__ import annotations

import json as std_json
from dataclasses import dataclass
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

import pytest
from requests import Response

import gateway_api.controller as controller_module
from gateway_api.controller import (
    Controller,
    SdsSearchResults,
)

if TYPE_CHECKING:
    from gateway_api.common.common import json_str


# -----------------------------
# Helpers for request test data
# -----------------------------
def make_request_body(nhs_number: str = "9434765919") -> json_str:
    """
    Create a JSON request body string containing an ``"nhs-number"`` field.

    :param nhs_number: NHS number to embed in the request body.
    :returns: JSON string payload suitable for
        :meth:`gateway_api.controller.Controller.call_gp_provider`.
    """
    # Controller expects a JSON string containing an "nhs-number" field.
    return std_json.dumps({"nhs-number": nhs_number})


def make_headers(
    ods_from: str = "ORG1",
    trace_id: str = "trace-123",
) -> dict[str, str]:
    """
    Create the minimum required headers for controller entry points.

    :param ods_from: Value for the ``Ods-from`` header (consumer ODS code).
    :param trace_id: Value for the ``X-Request-ID`` header (trace/correlation ID).
    :returns: Header dictionary suitable for
        :meth:`gateway_api.controller.Controller.call_gp_provider`.
    """
    # Controller expects these headers:
    # - Ods-from (consumer ODS)
    # - X-Request-ID (trace id)
    return {"Ods-from": ods_from, "X-Request-ID": trace_id}


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
    # We only need .gp_ods_code for controller logic.
    return SimpleNamespace(gp_ods_code=gp_ods_code)


class FakePdsClient:
    """
    Test double for :class:`gateway_api.pds_search.PdsClient`.

    The controller instantiates this class and calls ``search_patient_by_nhs_number``.
    Tests configure the returned patient details using ``set_patient_details``.
    """

    last_init: dict[str, Any] | None = None

    def __init__(self, **kwargs: Any) -> None:
        """
        Capture constructor kwargs for later assertions.

        :param kwargs: Arbitrary keyword arguments passed by the controller.
        """
        # Controller constructs PdsClient with kwargs; capture for assertions.
        FakePdsClient.last_init = dict(kwargs)
        self._patient_details: Any | None = None

    def set_patient_details(self, value: Any) -> None:
        """
        Configure the value returned by ``search_patient_by_nhs_number``.

        :param value: Result-like object to return (or ``None`` to simulate not found).
        """
        # Keep call sites explicit and "correct": pass a PDS-result-like object.
        self._patient_details = value

    def search_patient_by_nhs_number(self, nhs_number: int) -> Any | None:
        """
        Return the configured patient details.

        :param nhs_number: NHS number requested (not used by the fake).
        :returns: Configured patient details or ``None``.
        """
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
        """
        Capture constructor arguments and initialise storage for org details.

        :param auth_token: Auth token passed by the controller.
        :param base_url: Base URL passed by the controller.
        :param timeout: Timeout passed by the controller.
        """
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
        """
        Configure the SDS lookup result for a given ODS code.

        :param ods_code: ODS code key.
        :param org_details: SDS details or ``None`` to simulate not found.
        """
        self._org_details_by_ods[ods_code] = org_details

    def get_org_details(self, ods_code: str) -> SdsSearchResults | None:
        """
        Retrieve configured org details for a given ODS code.

        :param ods_code: ODS code to look up.
        :returns: Configured SDS details or ``None``.
        """
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
        """
        Capture constructor arguments for later assertions.

        :param provider_endpoint: Provider endpoint passed by the controller.
        :param provider_asid: Provider ASID passed by the controller.
        :param consumer_asid: Consumer ASID passed by the controller.
        """
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
        """
        Return either a configured :class:`requests.Response` or ``None``.

        :param trace_id: Trace identifier from request headers.
        :param body: JSON request body.
        :returns: A configured :class:`requests.Response`, or ``None`` if
            ``return_none`` is set.
        """
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

    Used in tests to set up SDS responses for provider and consumer orgs.
    """

    def __init__(
        self,
        org1: SdsSetup | None = None,
        org2: SdsSetup | None = None,
    ) -> None:
        """
        Construct the fake SDS client and configure org details.

        :param org1: First organisation to configure, or ``None``.
        :param org2: Second organisation to configure, or ``None``.
        :param kwargs: Additional keyword arguments passed to
            :class:`FakeSdsClient`.
        """
        self.org1 = org1
        self.org2 = org2
        # TODO: Fix factory class docstrings

    def __call__(self, **kwargs: Any) -> FakeSdsClient:
        """
        Return the configured fake SDS client.

        :returns: Configured :class:`FakeSdsClient` instance.
        """
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
        """
        Construct the fake PDS client and configure patient details.

        :param ods_code: Provider ODS code to set on the patient details.
        :param kwargs: Additional keyword arguments passed to
            :class:`FakePdsClient`.
        """
        self.ods_code = ods_code

    def __call__(self, **kwargs: Any) -> FakePdsClient:
        """
        Return the configured fake PDS client.

        :returns: Configured :class:`FakePdsClient` instance.
        """
        self.inst = FakePdsClient(**kwargs)
        self.inst.set_patient_details(_make_pds_result(self.ods_code))
        return self.inst


@pytest.fixture
def patched_deps(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Patch controller dependencies to use test fakes.
    Pass as a fixture to give any given test a clean set of patched dependencies.

    :param monkeypatch: pytest monkeypatch fixture.
    """
    # Patch dependency classes in the *module* namespace that Controller uses.
    monkeypatch.setattr(controller_module, "PdsClient", FakePdsClient)
    monkeypatch.setattr(controller_module, "SdsClient", FakeSdsClient)
    monkeypatch.setattr(controller_module, "GpProviderClient", FakeGpProviderClient)


@pytest.fixture
def controller() -> Controller:
    """
    Construct a controller instance configured for unit tests.

    :returns: Controller instance.
    """
    return Controller(
        pds_base_url="https://pds.example",
        sds_base_url="https://sds.example",
        nhsd_session_urid="session-123",
        timeout=3,
    )


# -----------------------------
# Unit tests
# -----------------------------


def test_call_gp_provider_returns_200_on_success(
    patched_deps: Any,
    monkeypatch: pytest.MonkeyPatch,
    controller: Controller,
) -> None:
    """
    On successful end-to-end call, the controller should return 200 with
    expected body/headers.
    """
    # TODO: OK, this works. Repeat it sixteen more times (or get the AI to do it)
    pds = pds_factory(ods_code="A12345")
    sds_org1 = SdsSetup(
        ods_code="A12345",
        search_results=SdsSearchResults(
            asid="asid_A12345", endpoint="https://provider.example/ep"
        ),
    )
    sds_org2 = SdsSetup(
        ods_code="ORG1",
        search_results=SdsSearchResults(asid="asid_ORG1", endpoint=None),
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

    body = make_request_body("9434765919")
    headers = make_headers()

    r = controller.run(body, headers, "token-abc")

    assert r.status_code == 200
    assert r.data == '{"resourceType":"Bundle"}'
    assert r.headers is not None
    assert r.headers.get("Content-Type") == "application/fhir+json"
    assert r.headers.get("X-Downstream") == "gp-provider"


def test_call_gp_provider_returns_404_when_pds_patient_not_found(
    patched_deps: Any,
    controller: Controller,
) -> None:
    """
    If PDS returns no patient record, the controller should return 404.
    """

    # No users added to the PDS stub, so a request for this user will get nothing
    # back from "PDS". The controller should return 404 with the given error.
    body = make_request_body("9434765919")
    headers = make_headers()

    r = controller.run(body, headers, "token-abc")

    assert r.status_code == 404
    assert "No PDS patient found for NHS number" in (r.data or "")


def test_call_gp_provider_returns_404_when_gp_ods_code_missing(
    patched_deps: Any,
    monkeypatch: pytest.MonkeyPatch,
    controller: Controller,
) -> None:
    """
    If PDS returns a patient without a provider (GP) ODS code, return 404.

    :param monkeypatch: pytest monkeypatch fixture.
    """
    pds = pds_factory(ods_code="")
    monkeypatch.setattr(controller_module, "PdsClient", pds)

    body = make_request_body("9434765919")
    headers = make_headers()

    r = controller.run(body, headers, "token-abc")

    assert r.status_code == 404
    assert "did not contain a current provider ODS code" in (r.data or "")


def test_call_gp_provider_returns_404_when_sds_returns_none_for_provider(
    patched_deps: Any,
    monkeypatch: pytest.MonkeyPatch,
    controller: Controller,
) -> None:
    """
    If SDS returns no provider org details, the controller should return 404.

    :param monkeypatch: pytest monkeypatch fixture.
    """
    pds = pds_factory(ods_code="A12345")
    sds = sds_factory()

    monkeypatch.setattr(controller_module, "PdsClient", pds)
    monkeypatch.setattr(controller_module, "SdsClient", sds)

    body = make_request_body("9434765919")
    headers = make_headers()

    r = controller.run(body, headers, "token-abc")

    assert r.status_code == 404
    assert r.data == "No SDS org found for provider ODS code A12345"


def test_call_gp_provider_returns_404_when_sds_provider_asid_blank(
    patched_deps: Any,
    monkeypatch: pytest.MonkeyPatch,
    controller: Controller,
) -> None:
    """
    If provider ASID is blank/whitespace, the controller should return 404.

    :param monkeypatch: pytest monkeypatch fixture.
    """
    pds = pds_factory(ods_code="A12345")
    sds_org1 = SdsSetup(
        ods_code="A12345",
        search_results=SdsSearchResults(
            asid="   ", endpoint="https://provider.example/ep"
        ),
    )
    sds = sds_factory(org1=sds_org1)

    monkeypatch.setattr(controller_module, "PdsClient", pds)
    monkeypatch.setattr(controller_module, "SdsClient", sds)

    body = make_request_body("9434765919")
    headers = make_headers()

    r = controller.run(body, headers, "token-abc")

    assert r.status_code == 404
    assert "did not contain a current ASID" in (r.data or "")


def test_call_gp_provider_returns_502_when_gp_provider_returns_none(
    patched_deps: Any,
    monkeypatch: pytest.MonkeyPatch,
    controller: Controller,
) -> None:
    """
    If GP provider returns no response object, the controller should return 502.

    :param monkeypatch: pytest monkeypatch fixture.
    """
    pds = pds_factory(ods_code="A12345")
    sds_org1 = SdsSetup(
        ods_code="A12345",
        search_results=SdsSearchResults(
            asid="asid_A12345", endpoint="https://provider.example/ep"
        ),
    )
    sds_org2 = SdsSetup(
        ods_code="ORG1",
        search_results=SdsSearchResults(asid="asid_ORG1", endpoint=None),
    )
    sds = sds_factory(org1=sds_org1, org2=sds_org2)

    monkeypatch.setattr(controller_module, "PdsClient", pds)
    monkeypatch.setattr(controller_module, "SdsClient", sds)

    FakeGpProviderClient.return_none = True

    body = make_request_body("9434765919")
    headers = make_headers()

    r = controller.run(body, headers, "token-abc")

    assert r.status_code == 502
    assert r.data == "GP provider service error"
    assert r.headers is None

    # reset for other tests
    FakeGpProviderClient.return_none = False


def test_call_gp_provider_constructs_pds_client_with_expected_kwargs(
    patched_deps: Any,
    controller: Controller,
) -> None:
    """
    Validate that the controller constructs the PDS client with expected kwargs.
    """

    body = make_request_body("9434765919")
    headers = make_headers(ods_from="ORG1", trace_id="trace-123")

    _ = controller.run(body, headers, "token-abc")  # will stop at PDS None => 404

    assert FakePdsClient.last_init is not None
    assert FakePdsClient.last_init["auth_token"] == "token-abc"  # noqa: S105
    assert FakePdsClient.last_init["end_user_org_ods"] == "ORG1"
    assert FakePdsClient.last_init["base_url"] == "https://pds.example"
    assert FakePdsClient.last_init["nhsd_session_urid"] == "session-123"
    assert FakePdsClient.last_init["timeout"] == 3


def test_call_gp_provider_returns_400_when_request_body_not_valid_json(
    patched_deps: Any,
    controller: Controller,
) -> None:
    """
    If the request body is invalid JSON, the controller should return 400.
    """
    headers = make_headers()

    r = controller.run("{", headers, "token-abc")

    assert r.status_code == 400
    assert r.data == "Request body must be valid JSON"


def test_call_gp_provider_returns_400_when_request_body_is_not_an_object(
    patched_deps: Any,
    controller: Controller,
) -> None:
    """
    If the request body JSON is not an expected type of object (e.g., list), return 400.
    """
    headers = make_headers()

    r = controller.run('["9434765919"]', headers, "token-abc")

    assert r.status_code == 400
    assert r.data == "JSON structure must be an object/dictionary"


def test_call_gp_provider_returns_400_when_request_body_missing_nhs_number(
    patched_deps: Any,
    controller: Controller,
) -> None:
    """
    If the request body omits ``"nhs-number"``, return 400.
    """
    headers = make_headers()

    r = controller.run("{}", headers, "token-abc")

    assert r.status_code == 400
    assert r.data == 'Missing required field "nhs-number" in JSON request body'


def test_call_gp_provider_returns_400_when_nhs_number_not_coercible(
    patched_deps: Any,
    controller: Controller,
) -> None:
    """
    If ``"nhs-number"`` cannot be coerced/validated, return 400.
    """
    headers = make_headers()

    r = controller.run(std_json.dumps({"nhs-number": "ABC"}), headers, "token-abc")

    assert r.status_code == 400
    assert r.data == 'Could not cast NHS number "ABC" to an integer'


def test_call_gp_provider_returns_400_when_missing_ods_from_header(
    patched_deps: Any,
    controller: Controller,
) -> None:
    """
    If the required ``Ods-from`` header is missing, return 400.
    """
    body = make_request_body("9434765919")

    r = controller.run(body, {"X-Request-ID": "trace-123"}, "token-abc")

    assert r.status_code == 400
    assert r.data == 'Missing required header "Ods-from"'


def test_call_gp_provider_returns_400_when_ods_from_is_whitespace(
    patched_deps: Any,
    controller: Controller,
) -> None:
    """
    If the ``Ods-from`` header is whitespace-only, return 400.
    """
    body = make_request_body("9434765919")

    r = controller.run(
        body, {"Ods-from": "   ", "X-Request-ID": "trace-123"}, "token-abc"
    )

    assert r.status_code == 400
    assert r.data == 'Missing required header "Ods-from"'


def test_call_gp_provider_returns_400_when_missing_x_request_id(
    patched_deps: Any,
    controller: Controller,
) -> None:
    """
    If the required ``X-Request-ID`` header is missing, return 400.
    """
    body = make_request_body("9434765919")

    r = controller.run(body, {"Ods-from": "ORG1"}, "token-abc")

    assert r.status_code == 400
    assert r.data == "Missing required header: X-Request-ID"


def test_call_gp_provider_returns_404_when_sds_provider_endpoint_blank(
    patched_deps: Any,
    monkeypatch: pytest.MonkeyPatch,
    controller: Controller,
) -> None:
    """
    If provider endpoint is blank/whitespace, the controller should return 404.

    :param monkeypatch: pytest monkeypatch fixture.
    """
    pds = pds_factory(ods_code="A12345")
    sds_org1 = SdsSetup(
        ods_code="A12345",
        search_results=SdsSearchResults(asid="asid_A12345", endpoint="   "),
    )
    sds_org2 = SdsSetup(
        ods_code="ORG1",
        search_results=SdsSearchResults(asid="asid_ORG1", endpoint=None),
    )
    sds = sds_factory(org1=sds_org1, org2=sds_org2)

    monkeypatch.setattr(controller_module, "PdsClient", pds)
    monkeypatch.setattr(controller_module, "SdsClient", sds)

    r = controller.run(make_request_body("9434765919"), make_headers(), "token-abc")

    assert r.status_code == 404
    assert "did not contain a current endpoint" in (r.data or "")


def test_call_gp_provider_returns_404_when_sds_returns_none_for_consumer(
    patched_deps: Any,
    monkeypatch: pytest.MonkeyPatch,
    controller: Controller,
) -> None:
    """
    If SDS returns no consumer org details, the controller should return 404.

    :param monkeypatch: pytest monkeypatch fixture.
    """
    pds = pds_factory(ods_code="A12345")
    sds_org1 = SdsSetup(
        ods_code="A12345",
        search_results=SdsSearchResults(
            asid="asid_A12345", endpoint="https://provider.example/ep"
        ),
    )
    sds = sds_factory(org1=sds_org1)

    monkeypatch.setattr(controller_module, "PdsClient", pds)
    monkeypatch.setattr(controller_module, "SdsClient", sds)

    r = controller.run(
        make_request_body("9434765919"), make_headers(ods_from="ORG1"), "token-abc"
    )

    assert r.status_code == 404
    assert r.data == "No SDS org found for consumer ODS code ORG1"


def test_call_gp_provider_returns_404_when_sds_consumer_asid_blank(
    patched_deps: Any,
    monkeypatch: pytest.MonkeyPatch,
    controller: Controller,
) -> None:
    """
    If consumer ASID is blank/whitespace, the controller should return 404.

    :param monkeypatch: pytest monkeypatch fixture.
    """
    pds = pds_factory(ods_code="A12345")
    sds_org1 = SdsSetup(
        ods_code="A12345",
        search_results=SdsSearchResults(
            asid="asid_A12345", endpoint="https://provider.example/ep"
        ),
    )
    sds_org2 = SdsSetup(
        ods_code="ORG1",
        search_results=SdsSearchResults(asid="   ", endpoint=None),
    )
    sds = sds_factory(org1=sds_org1, org2=sds_org2)

    monkeypatch.setattr(controller_module, "PdsClient", pds)
    monkeypatch.setattr(controller_module, "SdsClient", sds)

    r = controller.run(
        make_request_body("9434765919"), make_headers(ods_from="ORG1"), "token-abc"
    )

    assert r.status_code == 404
    assert "did not contain a current ASID" in (r.data or "")


def test_call_gp_provider_passthroughs_non_200_gp_provider_response(
    patched_deps: Any,
    monkeypatch: pytest.MonkeyPatch,
    controller: Controller,
) -> None:
    """
    Validate that non-200 responses from GP provider are passed through.

    :param monkeypatch: pytest monkeypatch fixture.
    """
    pds = pds_factory(ods_code="A12345")
    sds_org1 = SdsSetup(
        ods_code="A12345",
        search_results=SdsSearchResults(
            asid="asid_A12345", endpoint="https://provider.example/ep"
        ),
    )
    sds_org2 = SdsSetup(
        ods_code="ORG1",
        search_results=SdsSearchResults(asid="asid_ORG1", endpoint=None),
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

    r = controller.run(make_request_body("9434765919"), make_headers(), "token-abc")

    assert r.status_code == 404
    assert r.data == "Not Found"
    assert r.headers is not None
    assert r.headers.get("Content-Type") == "text/plain"
    assert r.headers.get("X-Downstream") == "gp-provider"
