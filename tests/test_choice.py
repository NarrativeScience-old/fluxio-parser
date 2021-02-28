"""Test choice."""
import unittest

from .util import StateTestCase


class TestChoiceState(StateTestCase):
    """Tests for the Choice state"""

    SUCCESSFUL_CASES = [
        (
            "Should parse NumericGreaterThan",
            """
def main(data):
    if data["foo"] > 10:
        return
""",
            {
                "StartAt": "Choice-276da054fcd7e7df19a6b12d8ccc5f0b",
                "States": {
                    "Choice-276da054fcd7e7df19a6b12d8ccc5f0b": {
                        "Type": "Choice",
                        "Choices": [
                            {
                                "Variable": "$['foo']",
                                "NumericGreaterThan": 10,
                                "Next": "Succeed-d1d0f861f06db686c59bfded9f95b5c4",
                            }
                        ],
                        "Default": "Pass-648ce2d5e0aec04ae8e97615f8a9efc8",
                    },
                    "Succeed-d1d0f861f06db686c59bfded9f95b5c4": {"Type": "Succeed"},
                    "Pass-648ce2d5e0aec04ae8e97615f8a9efc8": {
                        "Type": "Pass",
                        "End": True,
                    },
                },
            },
        ),
        (
            "Should parse NumericLessThan",
            """
def main(data):
    if data["foo"] < 10:
        return
""",
            {
                "StartAt": "Choice-08485f3ced31fa5f2f7d0ddb19c55354",
                "States": {
                    "Choice-08485f3ced31fa5f2f7d0ddb19c55354": {
                        "Type": "Choice",
                        "Choices": [
                            {
                                "Variable": "$['foo']",
                                "NumericLessThan": 10,
                                "Next": "Succeed-d1d0f861f06db686c59bfded9f95b5c4",
                            }
                        ],
                        "Default": "Pass-648ce2d5e0aec04ae8e97615f8a9efc8",
                    },
                    "Succeed-d1d0f861f06db686c59bfded9f95b5c4": {"Type": "Succeed"},
                    "Pass-648ce2d5e0aec04ae8e97615f8a9efc8": {
                        "Type": "Pass",
                        "End": True,
                    },
                },
            },
        ),
        (
            "Should handle explicit casting",
            """
def main(data):
    if int(data["foo"]) < 10:
        return
""",
            {
                "StartAt": "Choice-cf033f17919dc2e6b2d8b4650e19ed95",
                "States": {
                    "Choice-cf033f17919dc2e6b2d8b4650e19ed95": {
                        "Type": "Choice",
                        "Choices": [
                            {
                                "Variable": "$['foo']",
                                "NumericLessThan": 10,
                                "Next": "Succeed-d1d0f861f06db686c59bfded9f95b5c4",
                            }
                        ],
                        "Default": "Pass-648ce2d5e0aec04ae8e97615f8a9efc8",
                    },
                    "Succeed-d1d0f861f06db686c59bfded9f95b5c4": {"Type": "Succeed"},
                    "Pass-648ce2d5e0aec04ae8e97615f8a9efc8": {
                        "Type": "Pass",
                        "End": True,
                    },
                },
            },
        ),
        (
            "Should handle casted boolean",
            """
def main(data):
    if bool(data["foo"]):
        return
""",
            {
                "StartAt": "Choice-bc857240726fab55d8f7ee9191788ebc",
                "States": {
                    "Choice-bc857240726fab55d8f7ee9191788ebc": {
                        "Type": "Choice",
                        "Choices": [
                            {
                                "Variable": "$['foo']",
                                "BooleanEquals": True,
                                "Next": "Succeed-d1d0f861f06db686c59bfded9f95b5c4",
                            }
                        ],
                        "Default": "Pass-648ce2d5e0aec04ae8e97615f8a9efc8",
                    },
                    "Succeed-d1d0f861f06db686c59bfded9f95b5c4": {"Type": "Succeed"},
                    "Pass-648ce2d5e0aec04ae8e97615f8a9efc8": {
                        "Type": "Pass",
                        "End": True,
                    },
                },
            },
        ),
        (
            "Should handle explicit boolean",
            """
def main(data):
    if data["foo"] == False:
        return
""",
            {
                "StartAt": "Choice-379d4a4e3562a3feabbf0630d2944028",
                "States": {
                    "Choice-379d4a4e3562a3feabbf0630d2944028": {
                        "Type": "Choice",
                        "Choices": [
                            {
                                "Variable": "$['foo']",
                                "BooleanEquals": False,
                                "Next": "Succeed-d1d0f861f06db686c59bfded9f95b5c4",
                            }
                        ],
                        "Default": "Pass-648ce2d5e0aec04ae8e97615f8a9efc8",
                    },
                    "Succeed-d1d0f861f06db686c59bfded9f95b5c4": {"Type": "Succeed"},
                    "Pass-648ce2d5e0aec04ae8e97615f8a9efc8": {
                        "Type": "Pass",
                        "End": True,
                    },
                },
            },
        ),
        (
            "Should parse StringEquals",
            """
def main(data):
    if data["foo"] == "bar":
        return
""",
            {
                "StartAt": "Choice-d68055ebb717f7521db8c5b1a2e0dd09",
                "States": {
                    "Choice-d68055ebb717f7521db8c5b1a2e0dd09": {
                        "Type": "Choice",
                        "Choices": [
                            {
                                "Variable": "$['foo']",
                                "StringEquals": "bar",
                                "Next": "Succeed-d1d0f861f06db686c59bfded9f95b5c4",
                            }
                        ],
                        "Default": "Pass-648ce2d5e0aec04ae8e97615f8a9efc8",
                    },
                    "Succeed-d1d0f861f06db686c59bfded9f95b5c4": {"Type": "Succeed"},
                    "Pass-648ce2d5e0aec04ae8e97615f8a9efc8": {
                        "Type": "Pass",
                        "End": True,
                    },
                },
            },
        ),
        (
            "Should parse And",
            """
def main(data):
    if data["foo"] == "bar" and data["baz"] == 123:
        return
""",
            {
                "StartAt": "Choice-355b5b9796315e350071d83676dbba0d",
                "States": {
                    "Choice-355b5b9796315e350071d83676dbba0d": {
                        "Type": "Choice",
                        "Choices": [
                            {
                                "And": [
                                    {"Variable": "$['foo']", "StringEquals": "bar"},
                                    {"Variable": "$['baz']", "NumericEquals": 123},
                                ],
                                "Next": "Succeed-d1d0f861f06db686c59bfded9f95b5c4",
                            }
                        ],
                        "Default": "Pass-648ce2d5e0aec04ae8e97615f8a9efc8",
                    },
                    "Succeed-d1d0f861f06db686c59bfded9f95b5c4": {"Type": "Succeed"},
                    "Pass-648ce2d5e0aec04ae8e97615f8a9efc8": {
                        "Type": "Pass",
                        "End": True,
                    },
                },
            },
        ),
        (
            "Should parse Or",
            """
def main(data):
    if data["foo"] == "bar" or data["baz"] == 123:
        return
""",
            {
                "StartAt": "Choice-3febdfc9fe94cc76e0a7fd42240d2d1b",
                "States": {
                    "Choice-3febdfc9fe94cc76e0a7fd42240d2d1b": {
                        "Type": "Choice",
                        "Choices": [
                            {
                                "Or": [
                                    {"Variable": "$['foo']", "StringEquals": "bar"},
                                    {"Variable": "$['baz']", "NumericEquals": 123},
                                ],
                                "Next": "Succeed-d1d0f861f06db686c59bfded9f95b5c4",
                            }
                        ],
                        "Default": "Pass-648ce2d5e0aec04ae8e97615f8a9efc8",
                    },
                    "Succeed-d1d0f861f06db686c59bfded9f95b5c4": {"Type": "Succeed"},
                    "Pass-648ce2d5e0aec04ae8e97615f8a9efc8": {
                        "Type": "Pass",
                        "End": True,
                    },
                },
            },
        ),
        (
            "Should parse Not",
            """
def main(data):
    if not (data["foo"] == "bar" or data["baz"] == 123):
        return
""",
            {
                "StartAt": "Choice-dfb29af45515f3e4e8c4d8f83b6434e1",
                "States": {
                    "Choice-dfb29af45515f3e4e8c4d8f83b6434e1": {
                        "Type": "Choice",
                        "Choices": [
                            {
                                "Not": {
                                    "Or": [
                                        {"Variable": "$['foo']", "StringEquals": "bar"},
                                        {"Variable": "$['baz']", "NumericEquals": 123},
                                    ]
                                },
                                "Next": "Succeed-d1d0f861f06db686c59bfded9f95b5c4",
                            }
                        ],
                        "Default": "Pass-648ce2d5e0aec04ae8e97615f8a9efc8",
                    },
                    "Succeed-d1d0f861f06db686c59bfded9f95b5c4": {"Type": "Succeed"},
                    "Pass-648ce2d5e0aec04ae8e97615f8a9efc8": {
                        "Type": "Pass",
                        "End": True,
                    },
                },
            },
        ),
        (
            "Should set default",
            """
def main(data):
    if data["foo"] > 10:
        return
    else:
        data["ok"] = True
""",
            {
                "StartAt": "Choice-d292a4ca529b55a0d8ef3499d9272295",
                "States": {
                    "Choice-d292a4ca529b55a0d8ef3499d9272295": {
                        "Type": "Choice",
                        "Choices": [
                            {
                                "Variable": "$['foo']",
                                "NumericGreaterThan": 10,
                                "Next": "Succeed-d1d0f861f06db686c59bfded9f95b5c4",
                            }
                        ],
                        "Default": "Pass-84ae586bc8dc302d0c55e89e761554fa",
                    },
                    "Succeed-d1d0f861f06db686c59bfded9f95b5c4": {"Type": "Succeed"},
                    "Pass-84ae586bc8dc302d0c55e89e761554fa": {
                        "Type": "Pass",
                        "Result": True,
                        "ResultPath": "$['ok']",
                        "End": True,
                    },
                },
            },
        ),
        (
            "Should parse multiple choices",
            """
def main(data):
    if data["foo"] > 1000:
        data["above-1000"] = True
    elif data["foo"] > 100:
        data["above-100"] = True
    elif data["foo"] > 10:
        data["above-10"] = True
    else:
        data["ok"] = True
""",
            {
                "StartAt": "Choice-bbf1dd9e28a3c106a6661f7e2949d9b6",
                "States": {
                    "Choice-bbf1dd9e28a3c106a6661f7e2949d9b6": {
                        "Type": "Choice",
                        "Choices": [
                            {
                                "Variable": "$['foo']",
                                "NumericGreaterThan": 1000,
                                "Next": "Pass-44e9d56ec9a429c9d6a49e83061f33e5",
                            },
                            {
                                "Variable": "$['foo']",
                                "NumericGreaterThan": 100,
                                "Next": "Pass-317809b871ede0e96f17708af095153a",
                            },
                            {
                                "Variable": "$['foo']",
                                "NumericGreaterThan": 10,
                                "Next": "Pass-a35f1bf2613c162f68bfaa8dbffd6a31",
                            },
                        ],
                        "Default": "Pass-84ae586bc8dc302d0c55e89e761554fa",
                    },
                    "Pass-44e9d56ec9a429c9d6a49e83061f33e5": {
                        "Type": "Pass",
                        "Result": True,
                        "ResultPath": "$['above-1000']",
                        "End": True,
                    },
                    "Pass-317809b871ede0e96f17708af095153a": {
                        "Type": "Pass",
                        "Result": True,
                        "ResultPath": "$['above-100']",
                        "End": True,
                    },
                    "Pass-a35f1bf2613c162f68bfaa8dbffd6a31": {
                        "Type": "Pass",
                        "Result": True,
                        "ResultPath": "$['above-10']",
                        "End": True,
                    },
                    "Pass-84ae586bc8dc302d0c55e89e761554fa": {
                        "Type": "Pass",
                        "Result": True,
                        "ResultPath": "$['ok']",
                        "End": True,
                    },
                },
            },
        ),
    ]

    UNSUPPORTED_CASES = [
        (
            "Should raise if no explicit casting on boolean",
            """
def main(data):
    if data["foo"]:
        return
""",
            "Invalid conditional",
        ),
        (
            "Should raise if multiple comparison operators",
            """
def main(data):
    if 0 < data["foo"] < 10:
        return
""",
            "comparison operator",
        ),
        (
            "Should raise if input data used as comparator",
            """
def main(data):
    if data["foo"] < data["bar"]:
        return
""",
            "Input data",
        ),
        (
            "Should raise if function not supported",
            """
def main(data):
    if foo(data["foo"]) < 10:
        return
""",
            "Function foo is not supported",
        ),
        (
            "Should raise if multiple arguments passed to casting function",
            """
def main(data):
    if int(data["foo"], "no") < 10:
        return
""",
            "Data type casting",
        ),
        (
            "Should raise if None is used in conditional",
            """
def main(data):
    if data["foo"] == None:
        return
""",
            "None",
        ),
        (
            "Should raise if unknown data type",
            """
def main(data):
    if data["foo"] == unknown:
        return
""",
            "Could not determine data type",
        ),
        (
            "Should raise if multiple states in else clause",
            """
def main(data):
    if data["foo"] == "ok":
        return
    else:
        data["one"] = 1
        data["two"] = 2
""",
            "`else` clause",
        ),
    ]


if __name__ == "__main__":
    unittest.main()
