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
        self.assertTrue(visitor.state_machine_visitors["main"].requires_infrastructure)
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
        self.assertTrue(visitor.state_machine_visitors["main"].requires_infrastructure)
        self.assertEqual(
            visitor.state_machine_visitors["main"].event_processor["processor"].id,
            "TestEventProcessor",
        )
