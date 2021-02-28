"""parallel cases"""
import unittest

from .util import StateTestCase


class TestParallelState(StateTestCase):
    """Tests for the Parallel state"""

    SUCCESSFUL_CASES = [
        (
            "Should include a parallel state with multiple branches",
            """
def branch1(data):
    data["b1"] = 1

def branch2(data):
    data["b2"] = 2

def branch3(data):
    data["b3"] = 3

def main(data):
    parallel(branch1, branch2, branch3)
""",
            {
                "StartAt": "Parallel-9d4513d05f143505f123136402dd6e52",
                "States": {
                    "Parallel-9d4513d05f143505f123136402dd6e52": {
                        "Type": "Parallel",
                        "Branches": [
                            {
                                "StartAt": "Pass-138382c0e2f7b2fccd4c38eb69eddfbf",
                                "States": {
                                    "Pass-138382c0e2f7b2fccd4c38eb69eddfbf": {
                                        "Type": "Pass",
                                        "ResultPath": "$['b1']",
                                        "Result": 1,
                                        "End": True,
                                    }
                                },
                            },
                            {
                                "StartAt": "Pass-2cfec1cd3806737b490759c8329a6d51",
                                "States": {
                                    "Pass-2cfec1cd3806737b490759c8329a6d51": {
                                        "Type": "Pass",
                                        "ResultPath": "$['b2']",
                                        "Result": 2,
                                        "End": True,
                                    }
                                },
                            },
                            {
                                "StartAt": "Pass-c7b9627cb30a003113ad3423c0f24262",
                                "States": {
                                    "Pass-c7b9627cb30a003113ad3423c0f24262": {
                                        "Type": "Pass",
                                        "ResultPath": "$['b3']",
                                        "Result": 3,
                                        "End": True,
                                    }
                                },
                            },
                        ],
                        "End": True,
                    }
                },
            },
        )
    ]

    UNSUPPORTED_CASES = [
        (
            "Should raise if an unknown branch function is provided",
            """
def branch1(data):
    return

def main(data):
    parallel(branch1, branch2)
""",
            "defined functions",
        ),
        (
            "Should raise if no branch functions are provided",
            """
def main(data):
    parallel()
""",
            "At least one",
        ),
    ]


if __name__ == "__main__":
    unittest.main()
