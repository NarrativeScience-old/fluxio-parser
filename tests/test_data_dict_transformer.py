"""Contains tests for the data_dict transformer module"""

import ast
import unittest

import astor
import black

from fluxio_parser.transformers import DataDictTransformer


class TestDataDictTransformer(unittest.TestCase):
    """Tests for the DataDictTransformer class"""

    def _test_transformation(self, before, after):
        """Assert that the ``before`` string transformed to the ``after`` string"""
        tree = ast.parse(before)
        tree = DataDictTransformer().visit(tree)
        source = black.format_str(
            astor.to_source(tree), mode=black.FileMode(line_length=88)
        )
        self.assertEqual(
            source, black.format_str(after, mode=black.FileMode(line_length=88))
        )

    def test_dict(self):
        """Should transform a nested dict"""
        before = """
{
    "foo": data["foo"],
    "items": {
        "nested": [{
            "key": data["a"]
        }]
    }
}
"""
        after = """
{
    "foo.$": "$['foo']",
    "items": {
        "nested": [{
            "key.$": "$['a']"
        }]
    }
}
"""
        self._test_transformation(before, after)
