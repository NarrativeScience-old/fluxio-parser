"""Contains the EventProcessorVisitor class"""

import ast


class EventProcessorVisitor(ast.NodeVisitor):
    """AST node visitor that parses an EventProcessor class in a .sfn file.

    The goal is to collect import statements and the run method code. These will be
    spliced into a package's entry point module.

    Example Task class::

        class MyEventProcessor(EventProcessor):
            pass

    """

    pass
