"""Provider contract tests to verify the Flask API meets the consumer contract.

This test suite verifies that the actual Flask provider implementation
satisfies the contracts defined by consumers.
"""

import os
import threading
from collections.abc import Generator
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import ClassVar

import pytest
import requests
from pact import Verifier


def get_mtls_cert() -> tuple[str, str] | None:
    cert_path = os.getenv("MTLS_CERT")
    key_path = os.getenv("MTLS_KEY")
    if not cert_path or not key_path:
        return None
    return (cert_path, key_path)


class MtlsProxyHandler(BaseHTTPRequestHandler):
    """
    A simple proxy that forwards requests to the target HTTPS URL
    attaching the mTLS client certificates.
    """

    target_base: ClassVar[str] = ""
    cert: ClassVar[tuple[str, str] | None] = None

    def do_proxy(self, method: str) -> None:
        if not self.target_base:
            self.send_error(500, "Target base URL not set")
            return

        url = f"{self.target_base}{self.path}"

        content_length_header = self.headers.get("Content-Length")
        content_length = int(content_length_header) if content_length_header else 0
        body = self.rfile.read(content_length) if content_length > 0 else None

        headers = {k: v for k, v in self.headers.items() if k.lower() != "host"}

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                data=body,
                cert=self.cert,
                verify=False,
                timeout=30,
            )

            self.send_response(response.status_code)
            for k, v in response.headers.items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(response.content)

        except Exception as e:
            self.send_error(500, f"Proxy Error: {str(e)}")

    def do_GET(self) -> None:
        self.do_proxy("GET")

    def do_POST(self) -> None:
        self.do_proxy("POST")

    def do_PUT(self) -> None:
        self.do_proxy("PUT")


@pytest.fixture(scope="module")
def mtls_proxy(base_url: str) -> Generator[str, None, None]:
    """
    Spins up a local HTTP server in a separate thread.
    Returns the URL of this local proxy.
    """
    MtlsProxyHandler.target_base = base_url
    MtlsProxyHandler.cert = get_mtls_cert()

    server = HTTPServer(("localhost", 0), MtlsProxyHandler)
    port = server.server_port
    proxy_url = f"http://localhost:{port}"

    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    yield proxy_url

    server.shutdown()


def test_provider_honors_consumer_contract(mtls_proxy: str) -> None:
    verifier = Verifier(
        name="GatewayAPIProvider",
    )

    verifier.add_transport(url=mtls_proxy)

    verifier.add_source(
        "tests/contract/pacts/GatewayAPIConsumer-GatewayAPIProvider.json"
    )

    verifier.verify()
