"""Exceptions for the py2sfn library"""
from typing import Any

import astor


class SFNError(Exception):
    """Base py2sfn exception"""

    pass


class UnsupportedOperation(SFNError, AssertionError):
    """Raised when an operation in a .sfn is not supported"""

    def __init__(self, message: str, node: Any) -> None:
        """
        Args:
            message: Error message
            node: AST node that was checked

        """
        self.node = node
        msg = f"""{message.rstrip('.')}.

Provided (Line {self.node.lineno}, Column {self.node.col_offset}):

{astor.to_source(node).strip()}"""
        super().__init__(msg)


def assert_supported_operation(assertion: bool, message: str, node: Any) -> None:
    """Raise UnsupportedOperation if the assertion is false

    Args:
        assertion: Boolean condition
        message: Error message
        node: AST node to check

    Raises:
        :py:exc:`.UnsupportedOperation` if the assertion is false

    """
    if not assertion:
        raise UnsupportedOperation(message, node)
