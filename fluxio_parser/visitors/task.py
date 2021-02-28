"""Contains AST visitor class used to parse a Task class"""
import ast
from typing import Any, Callable, NamedTuple, Set, Union

from ..exceptions import assert_supported_operation, UnsupportedOperation
from ..transformers import RunMethodTransformer
from ..util import GET_VALUE_MAP


class Attribute(NamedTuple):
    """Data class for a task class attribute schema"""

    #: Getter function for extracting the value from the AST node
    get_value: Callable  # noqa
    #: Default value if the attribute is not provided
    default_value: Any  # noqa
    #: Set of allowed values
    allowed_values: Set[Union[str, int]] = None  # noqa


# Map of task class attribute name to an attribute schema
ATTRIBUTE_MAP = {
    "service": Attribute(
        get_value=GET_VALUE_MAP[str],
        allowed_values={
            "lambda",
            "lambda:container",
            "lambda:pexpm-runner",
            "ecs",
            "ecs:worker",
            "codebuild",
        },
        default_value="lambda",
    ),
    "timeout": Attribute(get_value=GET_VALUE_MAP[int], default_value=300),
    # CPU value validation will occur in the ECS task builder. It's only relevant
    # for ECS.
    "cpu": Attribute(get_value=GET_VALUE_MAP[int], default_value=1024),
    # Memory value validation will occur in the task builders.
    "memory": Attribute(get_value=GET_VALUE_MAP[int], default_value=2048),
    # Build Spec is only relevant to CodeBuild tasks
    "build_spec": Attribute(get_value=GET_VALUE_MAP[dict], default_value=None),
    # Autoscaling attributes are only relevant to ECS Worker tasks
    "autoscaling_min": Attribute(get_value=GET_VALUE_MAP[int], default_value=0),
    "autoscaling_max": Attribute(get_value=GET_VALUE_MAP[int], default_value=10),
    # Specification, concurrency, and heartbeat_interval attributes are currently only
    # used by ECS Worker tasks
    "spec": Attribute(get_value=GET_VALUE_MAP[str], default_value=""),
    "concurrency": Attribute(
        get_value=GET_VALUE_MAP[int], allowed_values=set(range(1, 101)), default_value=1
    ),
    "heartbeat_interval": Attribute(get_value=GET_VALUE_MAP[int], default_value=None),
}


class TaskVisitor(ast.NodeVisitor):
    """AST node visitor that parses a Task class in a .sfn file.

    The goal is to collect import statements and the run method code. These will be
    spliced into a package's entry point module.

    Example Task class::

        class MyTask(Task):

            service = "ecs"

            async def run(event, context):
                return "result"

    """

    def __init__(self) -> None:
        self.run_method = None
        self.imports = []
        self.run_method_body = []
        # Set default attribute values
        self.attributes = {
            key: attribute.default_value for key, attribute in ATTRIBUTE_MAP.items()
        }

    def visit_AsyncFunctionDef(self, node) -> None:
        """Visit an async function definition.

        The only supported method is ``run``.

        """
        if node.name == "run":
            for item in node.body:
                if isinstance(item, (ast.Import, ast.ImportFrom)):
                    self.imports.append(item)
                else:
                    self.run_method_body.append(item)
            self.run_method = RunMethodTransformer().visit(node)
            return

        raise UnsupportedOperation(
            "Task classes should only define a `run` method", node
        )

    def visit_ClassDef(self, node) -> None:
        """Visit the class definition.

        This parses class attributes then recurs into the class methods.

        """
        for item in node.body:
            if isinstance(item, ast.Assign):
                key = item.targets[0].id
                if key in ATTRIBUTE_MAP:
                    attribute = ATTRIBUTE_MAP[key]
                    value = attribute.get_value(item.value)
                    if attribute.allowed_values is not None:
                        assert_supported_operation(
                            value in attribute.allowed_values,
                            f"Allowed values for class attribute {key} include:"
                            f" {', '.join([str(value) for value in attribute.allowed_values])}",
                            node,
                        )
                    self.attributes[key] = value

        self.generic_visit(node)
