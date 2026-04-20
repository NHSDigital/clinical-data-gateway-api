import copy
import os
import uuid
from typing import Any

from locust import HttpUser, between, events, task
from locust.env import Environment
from tests.conftest import DEFAULT_REQUEST_HEADERS, SIMPLE_PAYLOAD


class GatewayApiHealth(HttpUser):
    wait_time = between(1, 3)

    def on_start(self) -> None:
        token = os.environ.get("APIGEE_ACCESS_TOKEN", "")
        if token:
            self.client.headers["Authorization"] = f"Bearer {token}"

        mtls_cert = os.environ.get("MTLS_CERT")
        mtls_key = os.environ.get("MTLS_KEY")
        if mtls_cert and mtls_key:
            self.client.cert = (mtls_cert, mtls_key)

    @task
    def test_health(self) -> None:
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")

    @task
    def test_structured_record(self) -> None:
        headers = DEFAULT_REQUEST_HEADERS.copy()
        headers["Ssp-TraceID"] = str(uuid.uuid4())

        payload = copy.deepcopy(SIMPLE_PAYLOAD)

        with self.client.post(
            "/patient/$gpc.getstructuredrecord",
            json=payload,
            headers=headers,
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(
                    f"Failed with status {response.status_code}: {response.text}"
                )


@events.quitting.add_listener  # type: ignore
def fail_on_nfr(environment: Environment, **_kwargs: Any) -> None:
    if environment.stats.total.fail_ratio > 0.01:
        print("*** Test failed: Error rate exceeded 1% ***")
        environment.process_exit_code = 1

    elif environment.stats.total.get_response_time_percentile(0.95) > 500:
        print("*** Test failed: 95th percentile response time exceeded 500ms ***")
        environment.process_exit_code = 1

    else:
        print("*** All performance NFRs met ***")
