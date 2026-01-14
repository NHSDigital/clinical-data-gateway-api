"""Consumer contract tests using Pact for the gateway API.

This test suite acts as a consumer that defines the expected
interactions with the provider (the Flask API).
"""

import requests
from pact import Pact


class TestConsumerContract:
    """Consumer contract tests to define expected API behavior."""

    def test_get_hello_world(self) -> None:
        """Test the consumer's expectation of the hello world endpoint.

        This test defines the contract: when the consumer requests
        GET/PUT/POST/PATCH/TRACE/DELETE to the
        /2015-03-31/functions/function/invocations endpoint, with a payload of "World",
        a 200 response containing "Hello, World!" is returned.
        """
        pact = Pact(consumer="GatewayAPIConsumer", provider="GatewayAPIProvider")

        # Define the expected interaction
        (
            pact.upon_receiving("a request for the hello world message")
            .with_body({"payload": "World"})
            .with_request(
                method="POST",
                path="/2015-03-31/functions/function/invocations",
            )
            .will_respond_with(status=200)
            .with_body(
                {
                    "statusCode": 200,
                    "headers": {"Content-Type": "application/json"},
                    "body": "Hello, World!",
                },
                content_type="application/json",
            )
        )

        # Start the mock server and execute the test
        with pact.serve() as server:
            # Make the actual request to the mock provider
            response = requests.post(
                f"{server.url}/2015-03-31/functions/function/invocations",
                json={"payload": "World"},
                timeout=10,
            )

            # Verify the response matches expectations
            assert response.status_code == 200
            body = response.json()
            assert body["body"] == "Hello, World!"
            assert body["statusCode"] == 200
            assert body["headers"] == {"Content-Type": "application/json"}

        # Write the pact file after the test
        pact.write_file("tests/contract/pacts")

    def test_get_nonexistent_route(self) -> None:
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
        pact.write_file("tests/contract/pacts")
