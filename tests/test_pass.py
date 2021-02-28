"""Test pass successful case"""
import unittest

from .util import StateTestCase


class TestPassState(StateTestCase):
    """Tests for the Pass state"""

    SUCCESSFUL_CASES = [
        (
            "Should set values on a specific key",
            """
def main(data):
    data["string"] = "world"
    data["number"] = 123
    data["object"] = {"hello": "world"}
    data["array"] = [{"hello": "world"}]
""",
            {
                "StartAt": "Pass-03bf5ede6555ea5c588bbeefac566e24",
                "States": {
                    "Pass-03bf5ede6555ea5c588bbeefac566e24": {
                        "Type": "Pass",
                        "Result": "world",
                        "ResultPath": "$['string']",
                        "Next": "Pass-80e471cc98424bb66cb15b4e09bb13ae",
                    },
                    "Pass-80e471cc98424bb66cb15b4e09bb13ae": {
                        "Type": "Pass",
                        "Result": 123,
                        "ResultPath": "$['number']",
                        "Next": "Pass-45641afa7944c38ad7ef54f269a6f8c0",
                    },
                    "Pass-45641afa7944c38ad7ef54f269a6f8c0": {
                        "Type": "Pass",
                        "Result": {"hello": "world"},
                        "ResultPath": "$['object']",
                        "Next": "Pass-710c506c697cf3b4f9f249e1f3e0497b",
                    },
                    "Pass-710c506c697cf3b4f9f249e1f3e0497b": {
                        "Type": "Pass",
                        "Result": [{"hello": "world"}],
                        "ResultPath": "$['array']",
                        "End": True,
                    },
                },
            },
        ),
        (
            "Should update data with a dict",
            """
def main(data):
    data.update({"hello": "world"})
""",
            {
                "StartAt": "Pass-37174743a84146f442bbdb2642ce38b9",
                "States": {
                    "Pass-37174743a84146f442bbdb2642ce38b9": {
                        "Type": "Pass",
                        "Result": {"hello": "world"},
                        "ResultPath": "$",
                        "End": True,
                    }
                },
            },
        ),
        (
            "Should collapse a pass statement node if there's a next state",
            """
def main(data):
    pass
    data["number"] = 123
""",
            {
                "StartAt": "Pass-80e471cc98424bb66cb15b4e09bb13ae",
                "States": {
                    "Pass-80e471cc98424bb66cb15b4e09bb13ae": {
                        "Type": "Pass",
                        "Result": 123,
                        "ResultPath": "$['number']",
                        "End": True,
                    }
                },
            },
        ),
        (
            "Should not collapse a pass statement node if there's no next state",
            """
def main(data):
    pass
""",
            {
                "StartAt": "Pass-648ce2d5e0aec04ae8e97615f8a9efc8",
                "States": {
                    "Pass-648ce2d5e0aec04ae8e97615f8a9efc8": {
                        "End": True,
                        "Type": "Pass",
                    }
                },
            },
        ),
    ]

    UNSUPPORTED_CASES = [
        (
            "Should raise if value is not JSON-serializeable",
            """
def main(data):
    data["array"] = range(10)
""",
            "JSON-serializeable",
        ),
        (
            "Should raise if value is not JSON-serializeable",
            """
def main(data):
    data.update({"hello": range(10)})
""",
            "JSON-serializeable",
        ),
    ]


if __name__ == "__main__":
    unittest.main()
