"""Contains the classes that represent the AWS Step Functions Map State"""
import ast
from typing import Any, Dict, Optional, TYPE_CHECKING

from fluxio_parser.states.base import State
from fluxio_parser.util import (
    CallableOption,
    convert_input_data_ref,
    GET_VALUE_MAP,
    parse_options,
)

if TYPE_CHECKING:
    import networkx as nx

# Map of task option name to an option schema
OPTION_MAP = {
    "max_concurrency": CallableOption(
        value_type=ast.Num,
        value_type_label="integer",
        get_value=GET_VALUE_MAP[int],
        default_value=0,
    )
}


class MapState(State):
    """Map state.

    A Map state contains a state machine (iterator) that will be called for every item
    in a list. The list of items is passed to the input of the state.

    See: https://docs.aws.amazon.com/step-functions/latest/dg/amazon-states-language-map-state.html

    For example::

        def iterator_function(data):
            return

        map(data["items"], iterator_function)

    resolves to::

        {
            "Type": "Map",
            "ItemsPath": "$['items']",
            "Iterator": {
                "StartsAt": "Succeed",
                "States": {
                    "Succeed": {"Type": "Succeed"}
                }
            }
        }

    """

    def __init__(
        self,
        state_graph: "nx.DiGraph",
        key: str,
        ast_node: Any,
        iterator: "StateMachineVisitor",  # noqa: F821
    ) -> None:
        """Initializer

        Args:
            state_graph: DAG of state machine fragments with edges between them
            key: Key of the fragment in the state machine's States value. This only
                really applies to States, not generic fragments.
            ast_node: AST node for this fragment in the .sfn file
            iterator: State machine visitor for the iterator function

        """
        super().__init__(state_graph, key, ast_node)
        self.iterator = iterator
        self.options = parse_options(OPTION_MAP, ast_node.value)

    def _get_input_path(self) -> str:
        """Get the InputPath value for the map state

        The input path should point to an object with keys:
        * **key** -- key pointing to the collection of state data items stored in
          DynamoDB. This key would have been generated in an earlier task.
        * **items** -- list of items that will be fanned-out. The length of the list is
          more important than the contents of each item because we'll use the ``key``
          to fetch the actual item value from DynamoDB.

        Returns:
            input path string

        """
        if len(self.ast_node.value.args) > 0:
            return convert_input_data_ref(self.ast_node.value.args[0])

        return "$"

    def _get_result_path(self) -> Optional[str]:
        """Get the ResultPath value for the map state

        If the result path was not explicitly provided, return None to indicate that
        the the result should be discarded.

        Returns:
            result path string or None

        """
        if isinstance(self.ast_node, ast.Assign) and len(self.ast_node.targets) > 0:
            return convert_input_data_ref(self.ast_node.targets[0])

        return None

    def to_dict(self) -> Dict:
        """Return a serialized representation of the Map state"""
        data = {
            "Type": "Map",
            "Parameters": {
                # Pass along tracing metadata from the input data object
                "__trace.$": "$.__trace",
                # Set the path to the key pointing to the collection of state data
                # items stored in DynamoDB. ``key`` is the local key scoped to the
                # currently execution whereas ``partition_key`` is global across all
                # projects and executions.
                "items_result_table_name.$": f"{self._get_input_path()}.table_name",
                "items_result_partition_key.$": f"{self._get_input_path()}.partition_key",
                "items_result_key.$": f"{self._get_input_path()}.key",
                "context_index.$": "$$.Map.Item.Index",
                "context_value.$": "$$.Map.Item.Value",
            },
            "Iterator": self.iterator.to_dict(),
            # Set the path to the list of items to fan-out. The length of the list is
            # more important than the contents of each item because we'll use the
            # items_result_key/items_result_partition_key to fetch from DynamoDB.
            "ItemsPath": f"{self._get_input_path()}.items",
            "ResultPath": self._get_result_path(),
            "MaxConcurrency": self.options["max_concurrency"],
        }
        self._set_end_or_next(data)
        return data
