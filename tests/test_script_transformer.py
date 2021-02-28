import ast
import unittest

import astor
import black

from fluxio_parser.transformers import ScriptTransformer


class TestScriptTransformer(unittest.TestCase):
    """Tests for the ScriptTransformer class"""

    def _test_transformation(self, before, after):
        """Assert that the ``before`` string transformed to the ``after`` string"""
        tree = ast.parse(before)
        tree = ScriptTransformer().visit(tree)
        source = black.format_str(
            astor.to_source(tree), mode=black.FileMode(line_length=88)
        )
        self.assertEqual(
            source, black.format_str(after, mode=black.FileMode(line_length=88))
        )

    def test_no_run_exception(self):
        """Should not transform empty exception handler in run method"""
        before = after = """
class Test(Task):
    async def run(event, context):
        try:
            raise Foo()
        except:
            pass

def main(data):
    Test(key="test")
"""
        self._test_transformation(before, after)
