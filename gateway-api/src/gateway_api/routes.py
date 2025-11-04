from flask import Blueprint

router = Blueprint("gateway", __name__)


@router.route("/")
def hello() -> str:
    return "Hello, World!"
