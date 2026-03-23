"""Provider contract tests to verify the Flask API meets the consumer contract.

This test suite verifies that the actual Flask provider implementation
satisfies the contracts defined by consumers.
"""

from typing import Any
from urllib.parse import urlparse

import pytest
from pact import Verifier

from tests.conftest import Client


@pytest.mark.remote_only
def test_provider_honors_consumer_contract(get_headers: Any, client: Client) -> None:

    host = urlparse(client.base_url).hostname

    verifier = Verifier(name="GatewayAPIProvider", host=host)

    # Send requests directly to the API Gateway
    verifier.add_transport(url=client.base_url)

    # So the Verifier can authenticate with the APIM proxy
    verifier.add_custom_headers(get_headers)

    verifier.add_source(
        "tests/contract/pacts/GatewayAPIConsumer-GatewayAPIProvider.json"
    )

    verifier.verify()
