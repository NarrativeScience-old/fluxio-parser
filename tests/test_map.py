"""Test map cases"""
import unittest

from .util import StateTestCase


class TestMapState(StateTestCase):
    """Tests for the Map state"""

    SUCCESSFUL_CASES = [
        (
            "Should include a map state with basic item iterator",
            """
def iterator(data):
    data["hello"] = "item"

def main(data):
    map(data["items"], iterator)
""",
            {
                "StartAt": "Map-19f3471bc82fa4a11de926d5c9f33621",
                "States": {
                    "Map-19f3471bc82fa4a11de926d5c9f33621": {
                        "Type": "Map",
                        "Iterator": {
                            "StartAt": "Pass-3da8a5ceda1f34dab85ad6bf06ff6be8",
                            "States": {
                                "Pass-3da8a5ceda1f34dab85ad6bf06ff6be8": {
                                    "Type": "Pass",
                                    "ResultPath": "$['hello']",
                                    "Result": "item",
                                    "End": True,
                                }
                            },
                        },
                        "Parameters": {
                            "__trace.$": "$.__trace",
                            "context_index.$": "$$.Map.Item.Index",
                            "context_value.$": "$$.Map.Item.Value",
                            "items_result_table_name.$": "$['items'].table_name",
                            "items_result_partition_key.$": "$['items'].partition_key",
                            "items_result_key.$": "$['items'].key",
                        },
                        "ItemsPath": "$['items'].items",
                        "ResultPath": None,
                        "MaxConcurrency": 0,
                        "End": True,
                    }
                },
            },
        ),
        (
            "Should store the result of the map state on data",
            """
def iterator(data):
    return

def main(data):
    data["output"] = map(data["items"], iterator)
""",
            {
                "StartAt": "Map-f79b7b6415fa8d001a93f2c13914622c",
                "States": {
                    "Map-f79b7b6415fa8d001a93f2c13914622c": {
                        "Type": "Map",
                        "Iterator": {
                            "StartAt": "Succeed-b7c9b5ad5dd8922b4baa2aacebd32797",
                            "States": {
                                "Succeed-b7c9b5ad5dd8922b4baa2aacebd32797": {
                                    "Type": "Succeed"
                                }
                            },
                        },
                        "Parameters": {
                            "__trace.$": "$.__trace",
                            "context_index.$": "$$.Map.Item.Index",
                            "context_value.$": "$$.Map.Item.Value",
                            "items_result_table_name.$": "$['items'].table_name",
                            "items_result_partition_key.$": "$['items'].partition_key",
                            "items_result_key.$": "$['items'].key",
                        },
                        "ItemsPath": "$['items'].items",
                        "ResultPath": "$['output']",
                        "MaxConcurrency": 0,
                        "End": True,
                    }
                },
            },
        ),
        (
            "Should set the max concurrency option explicitly",
            """
def iterator(data):
    return

def main(data):
    map(data["items"], iterator, max_concurrency=123)
""",
            {
                "StartAt": "Map-1e9f76b63455c2ef7c8c30c5a96a6202",
                "States": {
                    "Map-1e9f76b63455c2ef7c8c30c5a96a6202": {
                        "Type": "Map",
                        "Iterator": {
                            "StartAt": "Succeed-b7c9b5ad5dd8922b4baa2aacebd32797",
                            "States": {
                                "Succeed-b7c9b5ad5dd8922b4baa2aacebd32797": {
                                    "Type": "Succeed"
                                }
                            },
                        },
                        "Parameters": {
                            "__trace.$": "$.__trace",
                            "context_index.$": "$$.Map.Item.Index",
                            "context_value.$": "$$.Map.Item.Value",
                            "items_result_partition_key.$": "$['items'].partition_key",
                            "items_result_table_name.$": "$['items'].table_name",
                            "items_result_key.$": "$['items'].key",
                        },
                        "ItemsPath": "$['items'].items",
                        "ResultPath": None,
                        "MaxConcurrency": 123,
                        "End": True,
                    }
                },
            },
        ),
    ]

    UNSUPPORTED_CASES = [
        (
            "Should raise if no arguments are provided",
            """
def main(data):
    map()
""",
            "requires two arguments",
        ),
        (
            "Should raise if no iterator is provided",
            """
def main(data):
    map(data["items"])
""",
            "iterator function",
        ),
        (
            "Should raise if an unknown iterator is provided",
            """
def iterator(data):
    return

def main(data):
    map(data["items"], unknown_function)
""",
            "defined functions",
        ),
        (
            "Should raise if max concurrency option is not an int",
            """
def iterator(data):
    return

def main(data):
    map(data["items"], iterator, max_concurrency="123")
""",
            "Invalid data type",
        ),
    ]


if __name__ == "__main__":
    unittest.main()
