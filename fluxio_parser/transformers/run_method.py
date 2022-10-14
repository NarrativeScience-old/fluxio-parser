"""Contains an AST transformer class for processing Task class run methods"""
import ast
from typing import Any


class RunMethodTransformer(ast.NodeTransformer):
    """AST node transformer that removes import statements from a run method.

    Before this runs, we collect the run method's imports. We then clear out the
    imports so we can drop the run method body into the run.py module that we generated
    during the project build. This results in a properly formatted Python module
    (imports at the top, logic in the function).

    For example::

        async def run(event, context):
            import json
            from ns_python_core.config import CONFIG
            return json.dumps(CONFIG["foo"])

    will get transformed to::

        async def run(event, context):
            return json.dumps(CONFIG["foo"])
    """

    def visit_Import(self, node: Any) -> None:
        """Visit and remove the imports"""
        # Remove the import
        return None

    def visit_ImportFrom(self, node: Any) -> None:
        """Visit and remove the import from's"""
        # Remove the import
        return None
