"""Contains the classes that represent the AWS Step Functions Parallel State"""
from typing import Any, Dict, List, TYPE_CHECKING

import networkx as nx

from fluxio_parser.states.base import State

if TYPE_CHECKING:
    from fluxio_parser.visitors import StateMachineVisitor


class ParallelState(State):
    """Parallel state.

    A parallel state executes one or more branches in parallel. Each branch is a fully
    separate state machine defined in a module-level function. Branch functions are
    passed as positional arguments to the parallel function.

    See: https://docs.aws.amazon.com/step-functions/latest/dg/amazon-states-language-parallel-state.html

    For example::

        def branch1(data):
            return

        def branch2(data):
            return

        parallel(branch1, branch2)

    resolves to::

        {
            "Type": "Parallel",
            "Branches": [
                {
                    "StartsAt": "Succeed",
                    "States": {
                        "Succeed": {"Type": "Succeed"}
                    }
                },
                {
                    "StartsAt": "Succeed",
                    "States": {
                        "Succeed": {"Type": "Succeed"}
                    }
                }
            ]
        }
    """

    def __init__(self, state_graph: nx.DiGraph, key: str, ast_node: Any) -> None:
        """Initializer

        Args:
            state_graph: DAG of state machine fragments with edges between them
            key: Key of the fragment in the state machine's States value. This only
                really applies to States, not generic fragments.
            ast_node: AST node for this fragment in the .sfn file

        """
        super().__init__(state_graph, key, ast_node)
        self.branches = []

    def add_branch(self, branch: "StateMachineVisitor") -> "StateMachineVisitor":
        """Add a branch to the branch list

        Args:
            branch: Instance of a StateMachineVisitor that parsed the branch
                function definition

        Returns:
            the branch

        """
        self.branches.append(branch)
        return branch

    def to_dict(self) -> Dict:
        """Return a serialized representation of the Parallel state"""
        data = {"Type": "Parallel", "Branches": [b.to_dict() for b in self.branches]}
        self._set_end_or_next(data)
        return data

    @property
    def task_states(self) -> List[State]:
        """List of task state objects contained in all the branches"""
        return [state for branch in self.branches for state in branch.task_states]
