"""Contains the EventProcessorVisitor class"""

import ast
from typing import Any

from fluxio_parser.exceptions import assert_supported_operation, UnsupportedOperation


class EventProcessorVisitor(ast.NodeVisitor):
    """AST node visitor that parses an EventProcessor class in a .sfn file.

    The goal is to splice the class into a package's entry point module.

    Example EventProcessor class::

        class MyEventProcessor(EventProcessor):
            pass

    """

    def __init__(self, node: Any) -> None:
        """Initializer

        Args:
            node: AST node of the event processor class. Stored here for downstream
                processing.

        """
        super().__init__()
        self.node = node

    def visit_AsyncFunctionDef(self, node: Any) -> None:
        """Visit an async function definition.

        This validates that only a certain set of methods are defined, and they have the
        proper signatures.

        """
        assert_supported_operation(
            node.name.startswith("get_custom_tags_"),
            f"Custom event processors can only implement get_custom_tags_* methods. Provided: {node.name}",
            node,
        )
        arg_name_set = {arg.arg for arg in node.args.args}
        assert_supported_operation(
            arg_name_set == {"message", "input_data", "state_data_client"},
            "get_custom_tags_* methods must only accept positional arguments of"
            " (message, input_data, state_data_client)."
            f" Provided: {', '.join([arg.arg for arg in node.args.args])}",
            node,
        )

    def visit_FunctionDef(self, node: Any) -> None:
        """Visit a function definition

        Raise immediately because only async methods are allowed
        """
        raise UnsupportedOperation(
            f"Only async methods are allowed. Provided: {node.name}", node
        )
