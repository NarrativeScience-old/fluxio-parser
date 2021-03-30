"""Contains an AST class for modifying a dict that contains data references"""
import ast
from typing import Any

from fluxio_parser.util import convert_input_data_ref


class DataDictTransformer(ast.NodeTransformer):
    """AST node transformer that mutates a dict that contains data references

    For example, it transforms::

        {
            "foo": data["foo"],
            "items": {
                "nested": [{
                    "key": data["a"]
                }]
            }
        }

    into::

        {
            "foo.$": "$['foo']",
            "items": {
                "nested": [{
                    "key.$": "$['a']"
                }]
            }
        }

    """

    def visit_Dict(self, node: Any) -> None:
        """Visit a dict"""
        key_nodes = []
        value_nodes = []
        for key_node, value_node in zip(node.keys, node.values):
            if isinstance(value_node, ast.Subscript):
                key_nodes.append(ast.Str(s=f"{key_node.s}.$", ctx=ast.Load()))
                value_nodes.append(ast.Str(s=convert_input_data_ref(value_node)))
            else:
                key_nodes.append(self.generic_visit(key_node))
                value_nodes.append(self.generic_visit(value_node))

        return ast.copy_location(
            ast.Dict(keys=key_nodes, values=value_nodes, ctx=ast.Load()), node
        )

    def visit_Subscript(self, node: Any) -> None:
        """Visit a subscript"""
        return ast.copy_location(
            ast.Str(s=convert_input_data_ref(node), ctx=ast.Load()), node
        )
