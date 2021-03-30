"""Contains base classes used to represent AWS Step Functions States"""
from typing import Any, Dict, List

import astor
import networkx as nx

from fluxio_parser.util import hash_node


class StateMachineFragment:
    """State machine fragments represent some chunk of the state machine"""

    def __init__(self, state_graph: nx.DiGraph, key: str, ast_node: Any) -> None:
        """
        Args:
            state_graph: DAG of state machine fragments with edges between them
            key: Key of the fragment in the state machine's States value. This only
                really applies to States, not generic fragments.
            ast_node: AST node for this fragment in the .sfn file
        """
        self.state_graph = state_graph
        self.key = key
        self.ast_node = ast_node
        self._source = astor.to_source(ast_node).strip()
        self._hash = hash_node(ast_node)

    def __str__(self) -> str:
        """Returns string representation of the object"""
        return str(self.key)

    def __repr__(self) -> str:
        """Returns REPR representation of the object"""
        return f"{self.__class__.__name__}(key={self.key})"

    def _set_end_or_next(self, data: Dict) -> Dict:
        """Set the End or Next key on given dict depending on the outgoing edges

        This should be called in the to_dict method.

        Args:
            data: Dictionary currently being built in to_dict

        Returns:
            modified input data

        """
        edges = self.edges
        if len(edges) == 0:
            data["End"] = True
        else:
            data["Next"] = edges[-1].key

        return data

    def shape(self) -> None:
        """Shape the node or edges in the graph for this fragment.

        This is called after all states are loaded into the graph -- it's an optional
        post-processing step.

        Child classes may override this method.
        """
        pass

    def to_dict(self) -> Dict:
        """Return a serialized representation of the fragment.

        This output should be well-formed to be included in a state machine definition.

        Child classes should override this method.
        """
        return {}

    @property
    def edges(self) -> List[nx.classes.reportviews.OutEdgeView]:
        """Return a list of outgoing edges from this fragment node in the graph"""
        return list(self.state_graph[self])

    @property
    def descendants(self) -> List["StateMachineFragment"]:
        """Return a list of graph descendants starting from this fragment node"""
        # Create a new graph with only the dependencies so we can sort
        subgraph = nx.DiGraph(
            self.state_graph.subgraph(nx.descendants(self.state_graph, self))
        )
        descendants = list(nx.topological_sort(subgraph))
        return descendants


class State(StateMachineFragment):
    """Base class for state machine states

    This base State class only really exists to provide a more conceptually readable
    parent to the various subclasses in the states subpackage. State machine fragments
    that are not states include ChoiceBranch, parallel's Branch, and task's Catch.
    """

    #: Flag indicating if this is a terminal state, like Succeed or Fail
    TERMINAL = False
