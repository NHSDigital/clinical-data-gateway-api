from gateway_api.handler import User, greet


def handler(event: dict[str, str], context: dict[str, str]) -> dict[str, str]:
    print(f"Received event: {event}")
    user = User(name=event["payload"])
    return {"status_code": "200", "body": f"{greet(user)}"}
