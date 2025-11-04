import socket

from flask import Flask
from gateway_api.routes import router


def get_address() -> str:
    hostname = socket.gethostname()
    return socket.gethostbyname(hostname)


if __name__ == "__main__":
    app = Flask(__name__)
    app.register_blueprint(router)

    app.run(host=get_address(), port=5000)
