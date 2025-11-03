"""Consumer contract tests using Pact for the gateway API.

This test suite acts as a consumer that defines the expected
interactions with the provider (the Flask API).
"""

import requests
from pact import Pact


class TestConsumerContract:
    """Consumer contract tests to define expected API behavior."""

    def test_get_hello_world(self):
        """Test the consumer's expectation of the hello world endpoint.

        This test defines the contract: when the consumer requests
        GET / from the provider, they expect a 200 response with
        the message 'Hello, World!'.
        """
        pact = Pact(consumer="GatewayAPIConsumer", provider="GatewayAPIProvider")

        # Define the expected interaction
        (
            pact.upon_receiving("a request for the hello world message")
            .with_request(method="GET", path="/")
            .will_respond_with(status=200)
            .with_body("Hello, World!", content_type="text/html")
        )

        # Start the mock server and execute the test
        with pact.serve() as server:
            # Make the actual request to the mock provider
            response = requests.get(f"{server.url}/", timeout=10)

            # Verify the response matches expectations
            assert response.status_code == 200
            assert response.text == "Hello, World!"

        # Write the pact file after the test
        pact.write_file("tests/pacts")

    def test_get_nonexistent_route(self):
        """Test the consumer's expectation when requesting a non-existent route.

        This test defines the contract: when the consumer requests
        a route that doesn't exist, they expect a 404 response.
        """
        pact = Pact(consumer="GatewayAPIConsumer", provider="GatewayAPIProvider")

        # Define the expected interaction
        (
            pact.upon_receiving("a request for a non-existent route")
            .with_request(method="GET", path="/nonexistent")
            .will_respond_with(status=404)
        )

        # Start the mock server and execute the test
        with pact.serve() as server:
            # Make the actual request to the mock provider
            response = requests.get(f"{server.url}/nonexistent", timeout=10)

            # Verify the response matches expectations
            assert response.status_code == 404

        # Write the pact file after the test
        pact.write_file("tests/pacts")
