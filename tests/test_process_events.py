import ast
import unittest

from fluxio_parser import parse_project_tree


class TestProcessEvents(unittest.TestCase):
    """Tests for the process_events decorator"""

    def test_process_events__default(self):
        """Should parse the default processor"""
        code = """
@process_events()
def main(data):
    pass
"""
        visitor = parse_project_tree(ast.parse(code))
        self.assertDictEqual(visitor.event_processor_visitors, {})
        self.assertIsNone(
            visitor.state_machine_visitors["main"].event_processor["processor"]
        )

    def test_process_events__custom(self):
        """Should parse a custom processor"""
        code = """
class TestEventProcessor(EventProcessor):
    pass

@process_events(processor=TestEventProcessor)
def main(data):
    pass
"""
        visitor = parse_project_tree(ast.parse(code))
        self.assertIn("TestEventProcessor", visitor.event_processor_visitors)
        self.assertEqual(
            visitor.state_machine_visitors["main"].event_processor["processor"],
            "TestEventProcessor",
        )

    def test_process_events__multiple_state_machines(self):
        """Should parse a processor used by multiple state machines"""
        code = """
class TestEventProcessor(EventProcessor):
    pass

@process_events(processor=TestEventProcessor)
def one(data):
    pass

@process_events(processor=TestEventProcessor)
def two(data):
    pass
"""
        visitor = parse_project_tree(ast.parse(code))
        self.assertIn("TestEventProcessor", visitor.event_processor_visitors)
        self.assertEqual(
            visitor.state_machine_visitors["one"].event_processor["processor"],
            "TestEventProcessor",
        )
        self.assertEqual(
            visitor.state_machine_visitors["two"].event_processor["processor"],
            "TestEventProcessor",
        )

    def test_process_events__multiple_default(self):
        """Should parse multiple uses of the default processor"""
        code = """
@process_events()
def one(data):
    pass

@process_events()
def two(data):
    pass
"""
        visitor = parse_project_tree(ast.parse(code))
        self.assertDictEqual(visitor.event_processor_visitors, {})
        self.assertIsNone(
            visitor.state_machine_visitors["one"].event_processor["processor"]
        )
        self.assertIsNone(
            visitor.state_machine_visitors["two"].event_processor["processor"]
        )
