from flask import Flask

app = Flask(__name__)


@app.route("/")
def hello():
    return "Hello, World!"


# Temporary uncovered code to test coverage thresholds
def uncovered_function_one(x, y):
    """This function is not tested and should reduce coverage."""
    if x > y:
        return x * 2
    elif x < y:
        return y * 2
    else:
        return x + y


def uncovered_function_two(data):
    """Another untested function."""
    result = []
    for item in data:
        if item % 2 == 0:
            result.append(item * 10)
        else:
            result.append(item + 5)
    return result


class UncoveredClass:
    """Class with no test coverage."""

    def __init__(self, name):
        self.name = name
        self.count = 0

    def increment(self):
        self.count += 1
        return self.count

    def reset(self):
        self.count = 0
        return "Reset complete"
