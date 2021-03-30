"""Contains the main parser function"""

import ast

from fluxio_parser.transformers import ScriptTransformer
from fluxio_parser.visitors import ScriptVisitor


def parse_project_tree(
    project_tree: ast.Module, replace_empty_except: bool = True
) -> ScriptVisitor:
    """Parse the project's .sfn file.

    Args:
        project_tree: Parsed AST module
        replace_empty_except: Flag to control whether ``except:`` is replaced with
            ``States.ALL``. This should only be false when used in conjunction with
            another transformer, like LocalProjectRunnerTransformer.

    Returns:
        AST visitor containing objects collected from parsing project.sfn

    """
    tree = ScriptTransformer(replace_empty_except=replace_empty_except).visit(
        project_tree
    )
    visitor = ScriptVisitor()
    visitor.visit(tree)
    return visitor
