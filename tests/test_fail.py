"""Unit test module that holds a until for failed test state"""
import unittest

from .util import StateTestCase


class TestFailState(StateTestCase):
    """Tests for the Fail state"""

    SUCCESSFUL_CASES = [
        (
            "Should include Fail state for generic exception",
            """
def main(data):
    raise Exception()
""",
            {
                "StartAt": "Fail-cd3956f1344e049eb5b961b93cbe721b",
                "States": {
                    "Fail-cd3956f1344e049eb5b961b93cbe721b": {
                        "Type": "Fail",
                        "Cause": "Exception",
                        "Error": "Exception",
                    }
                },
            },
        ),
        (
            "Should include Fail state for generic exception with message",
            """
def main(data):
    raise Exception("oh no")
""",
            {
                "StartAt": "Fail-49418bbe3b87b98794227e1b921e20c7",
                "States": {
                    "Fail-49418bbe3b87b98794227e1b921e20c7": {
                        "Type": "Fail",
                        "Cause": "oh no",
                        "Error": "Exception",
                    }
                },
            },
        ),
        (
            "Should include Fail state for custom exception",
            """
def main(data):
    raise CustomError("oh no")
""",
            {
                "StartAt": "Fail-00d01613d1dc80efcc611f603c255725",
                "States": {
                    "Fail-00d01613d1dc80efcc611f603c255725": {
                        "Type": "Fail",
                        "Cause": "oh no",
                        "Error": "CustomError",
                    }
                },
            },
        ),
    ]


if __name__ == "__main__":
    unittest.main()
