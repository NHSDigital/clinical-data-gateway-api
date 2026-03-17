import os
import threading
from collections.abc import Generator
from functools import partial
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

import pytest
import requests


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

    def __init__(
        self,
        target_base: str,
        cert: tuple[str, str] | None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.target_base = target_base
        self.cert = cert
        super().__init__(*args, **kwargs)

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
                verify=False,  # NOQA S501 (No big deal in a test fixture)
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
def mtls_proxy(base_url: str) -> Generator[str]:
    """
    Spins up a local HTTP server in a separate thread.
    Returns the URL of this local proxy.
    """

    cert = get_mtls_cert()
    handler_factory = partial(MtlsProxyHandler, base_url, cert)
    server = HTTPServer(("localhost", 0), handler_factory)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    yield f"http://localhost:{server.server_port}"

    server.shutdown()
