"""Provider contract tests to verify the Flask API meets the consumer contract.

This test suite verifies that the actual Flask provider implementation
satisfies the contracts defined by consumers.
"""

from typing import Any

import pytest
from pact import Verifier


@pytest.mark.remote_only
class TestProviderContract:
    """Provider contract tests to verify the API implementation."""


def test_provider_honors_consumer_contract(mtls_proxy: str, get_headers: Any) -> None:

    verifier = Verifier(name="GatewayAPIProvider")

    verifier.add_transport(url=mtls_proxy)

    # So the Verifier can authenticate with the APIM proxy
    verifier.add_custom_headers(get_headers)

    verifier.add_source(
        "tests/contract/pacts/GatewayAPIConsumer-GatewayAPIProvider.json"
    )

    verifier.verify()
