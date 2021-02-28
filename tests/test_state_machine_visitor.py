"""State machine visitor unsupported test case"""
import unittest

from .util import StateTestCase


class TestStateMachineVisitor(StateTestCase):
    """Tests for generic syntax issues as parsed by the StateMachineVisitor"""

    UNSUPPORTED_CASES = [
        (
            "Should raise if assignment targets multiple variables",
            """
def main(data):
    data["a"], data["b"] = [1, 2]
""",
            "key on `data`",
        ),
        (
            "Should raise if assignment targets something other than data",
            """
def main(data):
    a = [1, 2]
""",
            "key on `data`",
        ),
        (
            "Should raise if a method other than update is called on data",
            """
def main(data):
    data.run()
""",
            "supported method call",
        ),
        (
            "Should raise on an unsupported expression",
            """
def main(data):
    foo()
""",
            "Supported expressions",
        ),
    ]


if __name__ == "__main__":
    unittest.main()
