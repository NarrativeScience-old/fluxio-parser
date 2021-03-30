"""Contains unit tests for the EventProcessorVisitor class"""
import ast
import unittest

from fluxio_parser.exceptions import UnsupportedOperation
from fluxio_parser.visitors import EventProcessorVisitor


class TestEventProcessorVisitor(unittest.TestCase):
    """Tests for the EventProcessorVisitor class"""

    def test_empty(self):
        """Should not fail when no methods"""
        code = """
class MyEventProcessor(EventProcessor):
    pass
"""
        tree = ast.parse(code)
        visitor = EventProcessorVisitor(tree)
        visitor.visit(tree)

    def test_ok(self):
        """Should not fail when proper methods set"""
        code = """
class MyEventProcessor(EventProcessor):
    async def get_custom_tags_Foo(message, input_data, state_data_client):
        pass

    async def get_custom_tags_Bar(message, input_data, state_data_client):
        pass
"""
        tree = ast.parse(code)
        visitor = EventProcessorVisitor(tree)
        visitor.visit(tree)

    def test_invalid_name(self):
        """Should raise on invalid method name"""
        code = """
class MyEventProcessor(EventProcessor):
    async def foo(message):
        pass
"""
        tree = ast.parse(code)
        visitor = EventProcessorVisitor(tree)
        with self.assertRaises(UnsupportedOperation):
            visitor.visit(tree)

    def test_invalid_signature(self):
        """Should raise on invalid method signature"""
        code = """
class MyEventProcessor(EventProcessor):
    async def get_custom_tags_Foo(message, bad):
        pass
"""
        tree = ast.parse(code)
        visitor = EventProcessorVisitor(tree)
        with self.assertRaises(UnsupportedOperation):
            visitor.visit(tree)

    def test_sync(self):
        """Should raise if sync function defined"""
        code = """
class MyEventProcessor(EventProcessor):
    def get_custom_tags_Foo(message):
        pass
"""
        tree = ast.parse(code)
        visitor = EventProcessorVisitor(tree)
        with self.assertRaises(UnsupportedOperation):
            visitor.visit(tree)
