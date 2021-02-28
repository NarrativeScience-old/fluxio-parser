"""Contains an AST transformer class for modifying an .sfn file"""
import ast
from typing import Any


class ScriptTransformer(ast.NodeTransformer):
    """AST node transformer that mutates a .sfn file before it's parsed.

    The goals of the transformer are to:
    * Replace empty ``except:`` statements with ``except States.ALL`` to match the
      StepFunctions spec
    * Add an explicit ``else`` clause if only ``if`` and ``elif`` exist. This makes it
      easier to parse the control flow in the StateMachineVisitor.
    """

    def __init__(self, replace_empty_except: bool = True, *args, **kwargs) -> None:
        """
        Args:
            replace_empty_except: Flag to control whether ``except:`` is replaced with
                ``States.ALL``. This should only be false when used in conjunction with
                another transformer, like LocalProjectRunnerTransformer.

        """
        super().__init__(*args, **kwargs)
        self.replace_empty_except = replace_empty_except
        self._current_base_class = None

    def visit_ClassDef(self, node: Any) -> None:
        """Visit a class definition

        We don't want to transform anything, just keep track of the current base class.
        """
        for base in node.bases:
            if base.id == "Task":
                self._current_base_class = base.id
                break

        return self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: Any) -> Any:
        """Visit an async function definition

        We don't want to transform anything, just ignore any processing of the run
        method.
        """
        if node.name == "run" and self._current_base_class == "Task":
            return node

        return self.generic_visit(node)

    def visit_ExceptHandler(self, node: Any) -> Any:
        """Visit an exception handler"""
        if self.replace_empty_except and node.type is None:
            return ast.copy_location(
                ast.ExceptHandler(
                    type=ast.Attribute(value=ast.Name(id="States"), attr="ALL"),
                    name=None,
                    body=node.body,
                    ctx=ast.Load(),
                ),
                node,
            )

        return node

    def visit_If(self, node: Any) -> Any:
        """Visit an if statement"""
        if len(node.orelse) == 0:
            node.orelse.append(ast.Pass())

        return self.generic_visit(node)
