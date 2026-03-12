#!/usr/bin/env python3

import argparse
import json
import os
import sys
from uuid import uuid4

import requests
from fhir.constants import FHIRSystem


def main() -> None:
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="POST request to GPC getstructuredrecord endpoint"
    )
    parser.add_argument(
        "nhs_number", help="NHS number to search for (e.g., 9690937278)"
    )
    args = parser.parse_args()

    # Check if BASE_URL is set
    base_url = os.environ.get("BASE_URL")
    if not base_url:
        print("Error: BASE_URL environment variable is not set")
        sys.exit(1)

    # Endpoint URL
    url = f"{base_url}/patient/$gpc.getstructuredrecord"

    # Request headers
    headers = {
        "Content-Type": "application/fhir+json",
        "Accept": "application/fhir+json",
        "Ssp-TraceID": str(uuid4()),
        "Ods-From": "S44444",
    }

    # Request body
    payload = {
        "resourceType": "Parameters",
        "parameter": [
            {
                "name": "patientNHSNumber",
                "valueIdentifier": {
                    "system": FHIRSystem.NHS_NUMBER,
                    "value": args.nhs_number,
                },
            }
        ],
    }

    # Make the POST request
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()

        print(f"Status Code: {response.status_code}")
        print(f"Response:\n{json.dumps(response.json(), indent=2)}")

    except requests.exceptions.RequestException as e:
        errtext = f"Error: {e}\n"
        if e.response is not None:
            errtext += f"Status Code: {e.response.status_code}\n"
            errtext += f"Response Body: {e.response.text}\n"
        print(errtext)
        sys.exit(1)


if __name__ == "__main__":
    main()
