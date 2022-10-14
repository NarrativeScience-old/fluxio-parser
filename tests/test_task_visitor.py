"""Test the task visitors"""
import ast
import unittest

from fluxio_parser.visitors import TaskVisitor


class TestTaskVisitor(unittest.TestCase):
    """Tests for the TaskVisitor class"""

    def test_parse_dependencies(self):
        """Should parse imports"""
        code = """
class Test(Task):
    async def run(event, context):
        import math
        from uuid import uuid4
        import black
        from ns_custom.nested import foo as bar

def main(data):
    Test(key="test")
"""
        visitor = TaskVisitor()
        visitor.visit(ast.parse(code))
        self.assertEqual(
            visitor.run_visitor.dependencies, {"math", "uuid", "black", "ns_custom"}
        )
