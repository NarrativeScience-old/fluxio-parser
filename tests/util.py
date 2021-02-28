"""Unit test utilities"""
import ast
import json
import logging
from typing import Dict, List, Tuple
import unittest

from fluxio_parser.exceptions import UnsupportedOperation
from fluxio_parser.transformers import ScriptTransformer
from fluxio_parser.visitors import ScriptVisitor


def get_state_machine(script, name="main"):
    """Get a state machine dict by name from a .sfn script"""
    tree = ScriptTransformer().visit(ast.parse(script))
    visitor = ScriptVisitor()
    visitor.visit(tree)
    state_machine = visitor.state_machine_visitors[name].to_dict()
    return state_machine


class StateTestCase(unittest.TestCase):
    """Base class for testing lists of test cases for a single state.

    Child classes can define:
    * **SUCCESSFUL_CASES**
    * **UNSUPPORTED_CASES**
    """

    #: Successful test cases correctly render state machine JSON. The list contains
    #: tuples with items:
    #: * Test case message (e.g. "Should ...")
    #: * Source code that would be in a .sfn file
    #: * Expected state machine output (a dict)
    SUCCESSFUL_CASES: List[Tuple[str, str, Dict]] = []
    #: Unsupported test cases are expected to raise UnsupportedOperation. The list
    #: contains tuples with items:
    #: * Test case message (e.g. "Should ...")
    #: * Source code that would be in a .sfn file
    #: * Part of the expected exception message (e.g. "Valid keyword")
    UNSUPPORTED_CASES: List[Tuple[str, str, str]] = []

    def test_successful_cases(self):
        """Test successful state machine cases"""
        self.maxDiff = None
        for message, source, output in self.SUCCESSFUL_CASES:
            with self.subTest():
                state_machine = get_state_machine(source)
                logging.debug(json.dumps(state_machine))
                self.assertEqual(state_machine, output, msg=message)

    def test_unsupported_cases(self):
        """Test unsupported state machine cases"""
        self.maxDiff = None
        for message, source, error in self.UNSUPPORTED_CASES:
            with self.subTest():
                with self.assertRaises(UnsupportedOperation, msg=message) as err:
                    logging.debug(json.dumps(get_state_machine(source)))
                self.assertIn(error, str(err.exception), msg=message)
