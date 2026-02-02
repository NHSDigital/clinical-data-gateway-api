import argparse
import sys
import uuid
from time import time

import jwt  # type: ignore
import requests


def print_auth_token(
    api_key: str, path_to_private_key: str, env: str = "internal-dev"
) -> None:
    auth_token_url = f"https://{env}.api.service.nhs.uk/oauth2/token"

    signed_jwt = sign_jwt(api_key, path_to_private_key, auth_token_url)

    response = request_auth_token(auth_token_url, signed_jwt)
    handle_auth_token_response(response)


def handle_auth_token_response(response):
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"Error obtaining auth token: {e}")
        print(response.text)
        sys.exit(1)
    else:
        token_response = response.json()
        print(token_response["access_token"])


def request_auth_token(auth_token_url, signed_jwt):
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    data = {
        "grant_type": "client_credentials",
        "client_assertion_type": (
            "urn:ietf:params:oauth:client-assertion-type:jwt-bearer"
        ),
        "client_assertion": signed_jwt,
    }

    response = requests.post(auth_token_url, headers=headers, data=data, timeout=10)
    return response


def sign_jwt(api_key, path_to_private_key, auth_token_url):
    with open(path_to_private_key) as f:
        private_key = f.read()

    five_minutes = int(time()) + 300
    claims = {
        "sub": api_key,
        "iss": api_key,
        "jti": str(uuid.uuid4()),
        "aud": auth_token_url,
        "exp": five_minutes,
    }

    key_id = get_key_id(path_to_private_key)
    additional_headers = {"kid": key_id}

    signed_jwt = jwt.encode(
        claims, private_key, algorithm="RS512", headers=additional_headers
    )

    return signed_jwt


def get_key_id(path_to_private_key: str) -> str:
    return path_to_private_key.split("/")[-1].split(".pem")[0]


def get_app_credentials(args) -> tuple[str, str, str]:
    parser = argparse.ArgumentParser(
        description=(
            "Take the application credentials and retrieve an auth token that "
            "can be passed in calls to the proxy."
        )
    )
    parser.add_argument(
        "api_key",
        help=(
            "The API key. This can be found in the app's Developer Account page, under "
            "'Edit API Keys'."
        ),
    )
    parser.add_argument(
        "path_to_private_key",
        help=(
            "The path to the private key file. The private key file should be named "
            "<key_id>.pem"
        ),
    )
    parser.add_argument(
        "--env",
        default="internal-dev",
        help="Environment in which the calling application lives",
    )
    args = parser.parse_args(args)

    return args.api_key, args.path_to_private_key, args.env


if __name__ == "__main__":
    program_arguments = sys.argv[1:]
    api_key, path_to_private_key, env = get_app_credentials(program_arguments)
    print_auth_token(api_key, path_to_private_key, env)
