"""Test wait successful case"""
import unittest

from .util import StateTestCase


class TestWaitState(StateTestCase):
    """Tests for the Wait state"""

    SUCCESSFUL_CASES = [
        (
            "Should wait for a literal number of seconds",
            """
def main(data):
    wait(seconds=123)
""",
            {
                "StartAt": "Wait-acfc0ffe21a7fc15fbd425f3f1ed7935",
                "States": {
                    "Wait-acfc0ffe21a7fc15fbd425f3f1ed7935": {
                        "Type": "Wait",
                        "Seconds": 123,
                        "End": True,
                    }
                },
            },
        ),
        (
            "Should wait for a number of seconds specified in a path",
            """
def main(data):
    wait(seconds=data["delay"])
""",
            {
                "StartAt": "Wait-f94b1942d6000010d52c2dbdd09d2be3",
                "States": {
                    "Wait-f94b1942d6000010d52c2dbdd09d2be3": {
                        "Type": "Wait",
                        "SecondsPath": "$['delay']",
                        "End": True,
                    }
                },
            },
        ),
        (
            "Should wait until a literal timestamp in the future",
            """
def main(data):
    wait(timestamp="2020-03-14T01:59:00Z")
""",
            {
                "StartAt": "Wait-2dd23feef2f381a3025040751022f634",
                "States": {
                    "Wait-2dd23feef2f381a3025040751022f634": {
                        "Type": "Wait",
                        "Timestamp": "2020-03-14T01:59:00Z",
                        "End": True,
                    }
                },
            },
        ),
        (
            "Should wait until a timestamp in the future specified in a path",
            """
def main(data):
    wait(timestamp=data["ts"])
""",
            {
                "StartAt": "Wait-22d8534042d1b9cad4eb8c277a9b6352",
                "States": {
                    "Wait-22d8534042d1b9cad4eb8c277a9b6352": {
                        "Type": "Wait",
                        "TimestampPath": "$['ts']",
                        "End": True,
                    }
                },
            },
        ),
    ]

    UNSUPPORTED_CASES = [
        (
            "Should raise if keyword argument is not supported",
            """
def main(data):
    wait(bad=data["ts"])
""",
            "Valid keyword",
        )
    ]


if __name__ == "__main__":
    unittest.main()
