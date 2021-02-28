"""Successful test case"""
import unittest

from .util import StateTestCase


class TestSucceedState(StateTestCase):
    """Tests for the Succeed state"""

    SUCCESSFUL_CASES = [
        (
            "Should include Succeed state",
            """
def main(data):
    return
""",
            {
                "StartAt": "Succeed-d1d0f861f06db686c59bfded9f95b5c4",
                "States": {
                    "Succeed-d1d0f861f06db686c59bfded9f95b5c4": {"Type": "Succeed"}
                },
            },
        )
    ]


if __name__ == "__main__":
    unittest.main()
