"""Contains the classes that represent the AWS Step Functions Choice State"""
import ast
from typing import Any, Dict, TYPE_CHECKING

from fluxio_parser.exceptions import assert_supported_operation, UnsupportedOperation
from fluxio_parser.states.base import State, StateMachineFragment
from fluxio_parser.util import convert_input_data_ref, hash_node

if TYPE_CHECKING:
    import networkx as nx

# Map of either:
# * tuple of:
#   ** AST comparison operator
#   ** Python data type
# * AST boolean operator
# to the Amazon States Language string representation
OP_TO_KEY = {
    (ast.Eq, str): "StringEquals",
    (ast.Lt, str): "StringLessThan",
    (ast.Gt, str): "StringGreaterThan",
    (ast.LtE, str): "StringLessThanEquals",
    (ast.GtE, str): "StringGreaterThanEquals",
    (ast.Eq, float): "NumericEquals",
    (ast.Lt, float): "NumericLessThan",
    (ast.Gt, float): "NumericGreaterThan",
    (ast.LtE, float): "NumericLessThanEquals",
    (ast.GtE, float): "NumericGreaterThanEquals",
    (ast.Eq, int): "NumericEquals",
    (ast.Lt, int): "NumericLessThan",
    (ast.Gt, int): "NumericGreaterThan",
    (ast.LtE, int): "NumericLessThanEquals",
    (ast.GtE, int): "NumericGreaterThanEquals",
    (ast.Eq, bool): "BooleanEquals",
    ast.Or: "Or",
    ast.And: "And",
    ast.Not: "Not",
}

# Map of the stringify built-in function name to the actual built-in function
TYPE_TO_CLASS = {"str": str, "int": int, "float": float, "bool": bool}


class ChoiceBranch(StateMachineFragment):
    """Choice branch state machine fragment

    Within a Choice state, this represents a single item in the array of Choices. Check
    out the ChoiceState class below for an example.
    """

    def _serialize(self, node: Any) -> Any:
        """Recursive function to serialize a part of the choice branch AST node.

        This looks at each part of the conditional statement's AST to determine the
        correct ASL representation.
        """
        if isinstance(node, ast.BoolOp):
            # e.g. ``___ and ___``
            return {
                OP_TO_KEY[node.op.__class__]: [
                    self._serialize(value) for value in node.values
                ]
            }
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            # e.g. ``not bool(data["foo"])``
            if isinstance(node.operand, ast.Call) and node.operand.func.id == "bool":
                value = {
                    "Variable": self._serialize(node.operand),
                    OP_TO_KEY[(ast.Eq, bool)]: True,
                }
            else:
                value = self._serialize(node.operand)
            return {"Not": value}
        elif isinstance(node, ast.Compare):
            # e.g. ``data["foo"] > 0``
            assert_supported_operation(
                len(node.ops) == 1,
                "Only 1 comparison operator at a time is allowed",
                node,
            )
            assert_supported_operation(
                len(node.comparators) == 1,
                "Only 1 comparator at a time is allowed",
                node,
            )
            op = node.ops[0]
            comparator = node.comparators[0]
            # Determine the data type of the choice
            type_ = None
            if isinstance(node.left, ast.Call):
                type_ = node.left.func.id
            if isinstance(comparator, ast.Call):
                assert_supported_operation(
                    type_ is None
                    or (type_ is not None and comparator.func.id == type_),
                    f"Value types must match. Found: {type_} {op.__class__}"
                    f" {comparator.func.id}",
                    node,
                )
                if type_ is None:
                    type_ = comparator.func.id
            elif isinstance(comparator, ast.Str):
                type_ = "str"
            elif isinstance(comparator, ast.Num):
                type_ = "float"
            elif isinstance(comparator, ast.NameConstant) and comparator.value in (
                True,
                False,
            ):
                type_ = "bool"
            elif isinstance(comparator, ast.Subscript):
                raise UnsupportedOperation(
                    "Input data cannot be used as the comparator (right side of operation)",
                    comparator,
                )
            else:
                raise UnsupportedOperation(
                    "Could not determine data type for choice variable", comparator
                )

            type_class = TYPE_TO_CLASS[type_]
            if isinstance(op, ast.NotEq):
                return {
                    "Not": {
                        "Variable": self._serialize(node.left),
                        OP_TO_KEY[(ast.Eq, type_class)]: self._serialize(comparator),
                    }
                }

            return {
                "Variable": self._serialize(node.left),
                OP_TO_KEY[(op.__class__, type_class)]: self._serialize(comparator),
            }

        elif isinstance(node, ast.Subscript):
            # e.g. ``data["foo"]``
            return convert_input_data_ref(node)
        elif isinstance(node, ast.Call):
            # e.g. ``int(data["foo"])``
            assert_supported_operation(
                node.func.id in TYPE_TO_CLASS,
                f"Function {node.func.id} is not supported. Allowed built-ins: "
                ", ".join(TYPE_TO_CLASS.keys()),
                node,
            )
            assert_supported_operation(
                len(node.args) == 1,
                "Data type casting functions only accept 1 positional argument",
                node,
            )
            if node.func.id == "bool":
                return {
                    "Variable": self._serialize(node.args[0]),
                    OP_TO_KEY[(ast.Eq, bool)]: True,
                }
            else:
                return self._serialize(node.args[0])
        elif isinstance(node, ast.NameConstant):
            assert_supported_operation(
                node.value is not None,
                "The value `None` is not allowed in Choice states",
                node,
            )
            return node.value
        elif isinstance(node, ast.Str):
            return node.s
        elif isinstance(node, ast.Num):
            return node.n

        raise UnsupportedOperation("Unsupported choice branch logic", node)

    def to_dict(self) -> Dict:
        """Return a serialized representation of the ChoiceBranch"""
        data = {}
        self._set_end_or_next(data)
        branch = self._serialize(self.ast_node.test)
        assert_supported_operation(
            isinstance(branch, dict),
            "Invalid conditional statement. Most likely there is no comparison or"
            " boolean logic present.",
            self.ast_node.test,
        )
        data.update(branch)
        return data


class ChoiceState(State):
    """Choice state

    A Choice state checks one or more boolean comparisons against the input data in
    order to determine the next state to transition to. Choice states are generated by
    using if/elif/else statements in an .sfn file.

    See: https://docs.aws.amazon.com/step-functions/latest/dg/amazon-states-language-choice-state.html

    For example::

        if data["foo"] >= 10:
            MyTask(key="at-least-10")
        elif data["foo"] < 0:
            MyTask(key="negative")
        else:
            MyTask(key="other")

    resolves to::

        {
            "Type": "Choice",
            "Choices": [
                {
                    "Variable": "$['foo']",
                    "NumericGreaterThanEquals": 10,
                    "Next": "at-least-10"
                },
                {
                    "Variable": "$['foo']",
                    "NumericLessThan": 0,
                    "Next": "negative"
                },
            ],
            "Default": "other"
        }
    """

    def __init__(self, state_graph: "nx.DiGraph", key: str, ast_node: Any) -> None:
        """Initializer

        Args:
            state_graph: DAG of state machine fragments with edges between them
            key: Key of the fragment in the state machine's States value. This only
                really applies to States, not generic fragments.
            ast_node: AST node for this fragment in the .sfn file

        """
        super().__init__(state_graph, key, ast_node)
        self.choice_branches = []
        self.current_choice_branch = None
        self.add_choice_branch(ast_node)

    def add_choice_branch(self, node: Any) -> ChoiceBranch:
        """Build a new choice branch and add it to the list of branches.

        This also updates the current choice branch pointer.

        Args:
            node: AST node representing a choice branch

        Returns:
            new ChoiceBranch instance

        """
        choice_branch = ChoiceBranch(
            self.state_graph, f"ChoiceBranch-{hash_node(node)}", node
        )
        self.choice_branches.append(choice_branch)
        self.current_choice_branch = choice_branch
        return choice_branch

    def shape(self) -> None:
        """Shape the graph for this Choice state node."""
        # Collect a list of nodes that are adjacent to this choice node in the graph
        # but are not linked via an edge with the ``in_else`` flag set to true. These
        # nodes represent the next state *after* the choice state.
        non_else_nodes = [
            node
            for node, edge_attrs in self.state_graph.adj[self].items()
            if not edge_attrs.get("in_else")
        ]
        assert_supported_operation(
            len(non_else_nodes) <= 1,
            "A maximum of 1 state can be downstream from a Choice state",
            self.ast_node,
        )
        if len(non_else_nodes) == 1:
            # For each choice branch, if it ends with a non-terminal state then add an
            # edge to the next state *after* the choice state.
            for branch in self.choice_branches:
                descendants = branch.descendants
                if len(descendants) > 0 and not descendants[-1].TERMINAL:
                    self.state_graph.add_edge(descendants[-1], non_else_nodes[0])

    def to_dict(self):
        """Return a serialized representation of the Choice state."""
        data = {
            "Type": "Choice",
            "Choices": [c.to_dict() for c in self.choice_branches],
        }

        # Collect a list of nodes that are adjacent to this choice node in the graph
        # that are linked via an edge with the ``in_else`` flag set to true. These
        # nodes represent the Default choice if none of the branches trigger.
        else_nodes = [
            node
            for node, edge_attrs in self.state_graph.adj[self].items()
            if edge_attrs.get("in_else")
        ]
        assert_supported_operation(
            len(else_nodes) <= 1,
            "A maximum of 1 state can be included in an `else` clause",
            self.ast_node,
        )
        if len(else_nodes) == 1:
            data["Default"] = else_nodes[0].key

        return data
