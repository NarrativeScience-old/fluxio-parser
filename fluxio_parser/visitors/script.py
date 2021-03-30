"""Contains AST visitor class used to parse a .sfn file"""
import ast
from collections import defaultdict
from typing import Any, Dict, Set

from fluxio_parser.exceptions import assert_supported_operation, UnsupportedOperation
from fluxio_parser.resource_decorators import RESOURCE_DECORATOR_MAP
from fluxio_parser.util import parse_options
from fluxio_parser.visitors.event_processor import EventProcessorVisitor
from fluxio_parser.visitors.state_machine import StateMachineVisitor
from fluxio_parser.visitors.task import TaskVisitor


class ScriptVisitor(ast.NodeVisitor):
    """AST node visitor for parsing the module-level of a .sfn file.

    The visitor's goals are to:
    * Collect Task class AST node visitors
    * Collect state machine visitor for each module-level function
    """

    def __init__(self) -> None:
        self.task_visitors: Dict[str, TaskVisitor] = {}
        self.state_machine_visitors: Dict[str, StateMachineVisitor] = {}
        self.event_processor_visitors: Dict[str, EventProcessorVisitor] = {}

    @property
    def dependencies(self) -> Set[str]:
        """Returns the full set of package dependencies across all tasks"""
        deps = set()
        for visitor in self.task_visitors.values():
            deps.update(visitor.run_visitor.dependencies)

        return deps

    def visit_ClassDef(self, node: Any) -> None:
        """Visit a class definition

        For each Task subclass, instantiate a visitor and visit it.
        """
        for base in node.bases:
            if base.id == "Task":
                visitor = TaskVisitor()
                visitor.visit(node)
                self.task_visitors[node.name] = visitor
                return
            elif base.id == "EventProcessor":
                visitor = EventProcessorVisitor(node)
                visitor.visit(node)
                self.event_processor_visitors[node.name] = visitor
                return

        raise UnsupportedOperation(
            "Only classes that inherit from Task or EventProcessor are supported", node
        )

    def visit_FunctionDef(self, node: Any) -> None:
        """Visit a function definition.

        Every module-level function is, to start, considered a full state machine.
        We'll determine later on whether the state machine is an embedded parallel
        branch, map iterator, or standalone state machine.
        """
        # Parse state machine options from the list of function decorators
        options = defaultdict(list)
        for decorator in node.decorator_list:
            key = decorator.func.id
            assert_supported_operation(
                isinstance(decorator, ast.Call) and key in RESOURCE_DECORATOR_MAP,
                "Supported resource decorators include:"
                f" {', '.join(RESOURCE_DECORATOR_MAP.keys())}",
                decorator,
            )
            decorator_config = RESOURCE_DECORATOR_MAP[key]
            options[key].append(
                parse_options(decorator_config["options"], decorator, visitor=self)
            )
            max_count = decorator_config.get("max_count")
            assert_supported_operation(
                max_count is None
                or (max_count is not None and len(options[key]) <= max_count),
                f"Only {max_count} @{key} decorators can be applied to a"
                " state machine function",
                node,
            )

        visitor = StateMachineVisitor(
            node.name, self.task_visitors, self.state_machine_visitors, **options
        )
        visitor.visit(node)
        visitor.shape_nodes()
        self.state_machine_visitors[node.name] = visitor
