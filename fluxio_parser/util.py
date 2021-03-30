"""Utility functions"""
import ast
import hashlib
import logging
import re
from typing import Any, Callable, Dict, NamedTuple, Optional

import astor

from fluxio_parser.exceptions import assert_supported_operation, UnsupportedOperation

logger = logging.getLogger(__name__)


def hash_node(node: Any, namespace: str = "") -> str:
    """Hash an AST node.

    NB: This is a naive way to hash. It doesn't need to be perfect in terms of avoiding
    collisions -- its purpose is to generate a key for a state -- but it's probably not
    sufficient.

    Args:
        node: AST node
        namespace: Arbitrary string to include in the hash. Usually this will be the
            name of the state machine visitor so the final output can delineate between
            nodes.

    Returns:
        hash of the node for use as a state key

    """
    return hashlib.md5(
        (
            namespace + "".join(astor.to_source(node).replace("\n", "").split(" "))
        ).encode()
    ).hexdigest()


def convert_input_data_ref(node: Any) -> str:
    """Convert an AST node referencing the input data object to the ``$`` form.

    Example::

        data["foo"] -> $["foo"]

    Args:
        node: AST node

    Returns:
        input data reference in ``$`` form

    """
    return re.sub("^data", "$", astor.to_source(node).strip())


def serialize_error_name(node: Any) -> str:
    """Serialize an exception node to a string.

    This can be something like ``MyError`` or ``States.Timeout``.

    Args:
        node: Exception node

    Returns:
        string representation of the error

    """
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute) and node.value.id == "States":
        return astor.to_source(node).strip()
    else:
        raise UnsupportedOperation(
            "Error handler must be a tuple of exception classes or a single"
            " exception class.",
            node,
        )


# Map of data type to a value getter function
GET_VALUE_MAP = {
    str: lambda node, visitor: node.s,
    int: lambda node, visitor: node.n,
    float: lambda node, visitor: node.n,
    bool: lambda node, visitor: node.value,
    dict: lambda node, visitor: ast.literal_eval(astor.to_source(node).strip()),
    list: lambda node, visitor: ast.literal_eval(astor.to_source(node).strip()),
}


class CallableOption(NamedTuple):
    """Data class for a Callable option.

    A Callable option is a class attribute or function call keyword argument.

    Example Callables include:
    * task states, e.g. MyTask(key="hello", timeout=10)
    * map states, e.g. map(data["items"], iterator, key="map it")
    * state machine function decorators, e.g. @schedule(expression="cron(0 12 * * ? *)")

    """

    #: Expected AST node type of the option value
    value_type: Any
    #: Label for the expected value type
    value_type_label: str
    #: Getter function for extracting the value from the AST node
    get_value: Callable[[Any, ast.NodeVisitor], Any]
    #: Default value if the option is not provided
    default_value: Any = None
    #: Flag indicating that this option is required
    required: bool = False


class OptionsMap(dict):
    """Wrapper around dict to store additional metadata like the originating AST node

    This will be used mostly for debugging and printing error messages.

    """

    def __init__(self, node: Any, *args, **kwargs) -> None:
        """Initialize an OptionsMap

        Args:
            node: AST node containing the options

        """
        super().__init__(*args, **kwargs)
        self.node = node


def parse_options(
    option_map: Dict[str, CallableOption],
    node: ast.Call,
    visitor: Optional[ast.NodeVisitor] = None,
) -> OptionsMap:
    """Parse options from keyword arguments passed to a Callable.

    See :py:class:`CallableOption`

    Args:
        option_map: Map of keyword argument name to the CallableOption schema
        node: AST node of the task state being added to the state machine
        visitor: Instance of a node visitor to provide extra context for parsing options

    Returns:
        OptionsMap instance, which is a dict of key-values with defaults filled in

    """
    options = OptionsMap(node)
    options.update(
        {
            key: option.default_value(node, visitor)
            if callable(option.default_value)
            else option.default_value
            for key, option in option_map.items()
        }
    )
    for keyword in node.keywords:
        key = keyword.arg
        assert_supported_operation(
            key in option_map,
            f"Invalid keyword argument. Options: {', '.join(option_map.keys())}",
            node,
        )
        option = option_map[key]
        if option.value_type:
            assert_supported_operation(
                isinstance(keyword.value, option.value_type),
                f"Invalid data type for the {key} option:"
                f" expected a {option.value_type_label}.",
                node,
            )
        value = option.get_value(keyword.value, visitor)
        options[key] = value

    # Ensure that all required options were provided
    required_options = {key for key, option in option_map.items() if option.required}
    provided_options = {keyword.arg for keyword in node.keywords}
    missing_options = required_options - provided_options
    assert_supported_operation(
        len(missing_options) == 0,
        f"The following options are required but were not provided: {', '.join(missing_options)}",
        node,
    )

    return options


def get_keyword_arg_value(
    node: ast.Call, keyword_name: str, default: Any = None
) -> Any:
    """Get a keyword arg value from a Call AST node

    Args:
        node: AST Call node, like a function call
        keyword_name: Name of the keyword argument
        default: Default value to return if the keyword was not found

    Returns:
        keyword argument value or default or None

    """
    for keyword in node.keywords:
        if keyword.arg == keyword_name:
            return keyword.value

    return default
