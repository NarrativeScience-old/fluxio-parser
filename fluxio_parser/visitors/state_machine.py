"""Contains AST visitor class used to parse a state machine definition"""
import ast
from collections import deque, OrderedDict
import logging
from typing import Any, Dict, List, Optional

import astor
import networkx as nx

from fluxio_parser.exceptions import assert_supported_operation, UnsupportedOperation
from fluxio_parser.states import (
    ChoiceState,
    create_task_state,
    FailState,
    MapState,
    ParallelState,
    PassState,
    State,
    SucceedState,
    TaskState,
    WaitState,
)
from fluxio_parser.util import hash_node


class StateMachineVisitor(ast.NodeVisitor):
    """AST node visitor for parsing a state machine function in a .sfn file.

    The main state machine function is called ``main``, but if a ``parallel`` or
    ``map`` state is used, then each branch is defined by a separate state machine
    function and will be parsed by this visitor.

    The visitor's goal is to build a directed acyclic graph (DAG) of states by visiting
    nodes in the state machine function AST.
    """

    def __init__(
        self,
        name: str,
        task_visitors: Dict[str, "TaskVisitor"],  # noqa
        state_machine_visitors: Dict[str, "StateMachineVisitor"],
        schedule: Optional[List[Dict]] = None,
        export: Optional[List[Dict]] = None,
        subscribe: Optional[List[Dict]] = None,
        process_events: Optional[List[Dict]] = None,
    ) -> None:
        """Initialize a state machine visitor

        Args:
            name: Name of the state machine, coming from the function defining its logic
            task_visitors: Map of Task class name to Task class AST node visitor
            state_machine_visitors: Map of function name to state machine AST
                node visitor
            schedule: List of dicts with schedule options containing keys:
                * **expression** -- cron or rate expression. See https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/ScheduledEvents.html
            export: List of dicts with export options containing keys:
                * **enabled** -- bool
            subscribe: List of dicts with subscribe options containing keys:
                * **topic_arn_import_value** -- CloudFormation import value string for
                  importing the topic ARN from another stack. Either this or ``project``
                  is required.
                * **project** -- Name of another project folder to import CF references.
                  Either this or ``topic_arn_import_value`` is required.
                * **state_machine** -- Name of state machine in the other project.
                  Defaults to "main". Only applies if ``project`` is specified.
                * **status** -- High-level execution status. One of success|failure.
                  Only applies if ``project`` is specified.
            process_events: List of dicts with event processor options containing keys:
                * **processor** -- Event processor class. If not provided, the default
                  event processor will be used

        """
        self.name = name
        self._task_visitors = task_visitors
        self._state_machine_visitors = state_machine_visitors
        self.schedule = schedule[0] if schedule is not None else None
        self.export = export[0] if export is not None else None
        self.subscribes = subscribe or []
        self.event_processor = process_events[0] if process_events is not None else None
        # The attributes are used when this visitor is included as a task state in
        # another state machine. We'll hard-code the service attribute so the correct
        # task state class is chosen in the factory.
        self.attributes = {"service": "state-machine"}
        # Begin with the current state set to this magic constant
        self._current_state = "__START__"
        # Initialize a stack for pushing and popping Choice states. This is used
        # because the AST for an if/elif/else node is recursively traversed but the
        # Choice state we need to build is a flat list. Start out with None to indicate
        # that we're not in a Choice node.
        self._choice_state_stack = deque([None])
        # Flag to tell if we're within a Choice state body. This is used to figure out
        # how to link together states.
        self._in_choice_body = False
        # Flag to tell if we're within an ``else`` node body. This will be used to set a
        # graph edge attribute.
        self._in_else = False
        # Initialize the DAG of states. Nodes represent state machine fragments
        # (usually states) and edges represent state transitions. The edges inform the
        # value of the Next key for a state.
        self.state_graph = nx.DiGraph()
        # Normalize the name to PascalCase so we can generate consistent CloudFormation
        # resources later on regardless of whether the state machine came from a
        # function or a class.
        self.normalized_name = self.name.title().replace(" ", "")
        # Set of other state machine (function) names available to be referenced in
        # this state machine
        self._other_state_machine_names = set(self._state_machine_visitors)
        # Flag denoting whether this object represents a first-class state machine that
        # should be given its own CloudFormation template, or if it's in service of a
        # Map state iterator or Parallel state branch. If it's the latter, we'll embed
        # the state machine in another one instead of creating separate infrastructure.
        # Nested state machines should always be first-class.
        self.is_first_class = True
        # Flag denoting whether this state machine is used as a map iterator
        self.is_map_iterator = False
        # CloudFormation logical resource ID
        self.cf_logical_id = f"{self.normalized_name}StateMachineStack"

    @property
    def task_states(self) -> List[TaskState]:
        """Returns list of currently registered task states"""
        states = []
        for state in list(self.state_graph.nodes):
            if isinstance(state, TaskState):
                states.append(state)
            elif isinstance(state, MapState):
                states.extend(state.iterator.task_states)
            elif isinstance(state, ParallelState):
                states.extend(state.task_states)

        return states

    def shape_nodes(self) -> None:
        """Shape each state node in the graph"""
        for state in list(self.state_graph.nodes):
            if isinstance(state, State):
                state.shape()

    def to_dict(self) -> Dict:
        """Serialize the state machine"""
        state_machine = {"StartAt": None, "States": OrderedDict()}
        for state in self.state_graph.nodes:
            if state == "__START__":
                # Set the starting state to be the key of the next state after __START__
                state_machine["StartAt"] = list(self.state_graph[state])[0].key
            elif isinstance(state, State):
                state_machine["States"][state.key] = state.to_dict()

        return state_machine

    def _add_state(self, state: State) -> None:
        """Add a new state to the graph

        Args:
            state: State to add

        """
        logging.debug(f"Adding edge from {self._current_state} -> {state}")
        self.state_graph.add_edge(self._current_state, state, in_else=self._in_else)

    def visit_Assign(self, node: Any) -> None:
        """Visit assignment nodes.

        Assignments are used to create Task and Pass states.

        Examples::

            data["result"] = Foo()
            data["result"] = map(data["items"], item_iterator)
            data["result"] = {"hello": "world"}

        """
        assert_supported_operation(
            len(node.targets) == 1,
            "Value assignments can only target one variable",
            node,
        )
        source = astor.to_source(node).strip()
        logging.debug(f"Visiting Assign ({source})")
        target = node.targets[0]
        assert_supported_operation(
            isinstance(target, ast.Subscript) and target.value.id == "data",
            "Assignment target must be a key on `data`",
            node,
        )
        if (
            isinstance(node.value, ast.Call)
            and node.value.func.id in self._task_visitors
        ):
            # This node is instantiating a task class
            state = create_task_state(
                self, node, self._task_visitors[node.value.func.id]
            )
            self._add_state(state)
            self._set_current_state(state)
        elif (
            isinstance(node.value, ast.Call)
            and node.value.func.id in self._state_machine_visitors
        ):
            # This node is nesting a state machine
            state = create_task_state(
                self, node, self._state_machine_visitors[node.value.func.id]
            )
            self._add_state(state)
            self._set_current_state(state)
        elif isinstance(node.value, ast.Call) and node.value.func.id == "map":
            # This node is instantiating a map state
            args = node.value.args
            assert_supported_operation(
                len(args) == 2,
                "Map state requires two arguments: a list of items from data and an"
                " iterator function",
                node,
            )
            _, iterator = args
            assert_supported_operation(
                isinstance(iterator, ast.Name)
                and iterator.id in self._state_machine_visitors,
                "Only defined functions can be provided to the map state."
                f" Available functions: {', '.join(self._other_state_machine_names)}",
                node,
            )
            state = MapState(
                self.state_graph,
                f"Map-{hash_node(node)}",
                node,
                self._state_machine_visitors[iterator.id],
            )
            self._add_state(state)
            self._set_current_state(state)
            # The referenced state machine is used as an iterator so we'll demote it
            self._state_machine_visitors[iterator.id].is_first_class = False
            self._state_machine_visitors[iterator.id].is_map_iterator = True
        else:
            # This node is setting static data
            state = PassState(
                self.state_graph, f"Pass-{hash_node(node, self.name)}", node
            )
            self._add_state(state)
            self._set_current_state(state)

    def visit_Expr(self, node: Any) -> None:
        """Visit expression nodes.

        Expressions are function calls that aren't assigned to a variable. These include:
        * ``update()`` for Pass states
        * ``parallel()`` for Parallel states
        * ``wait`` for Wait states
        * ``map`` for Map states
        * Instantiating Task classes

        Examples::

            data.update({"hello": "world"})
            parallel(branch1, branch2)
            wait(seconds=10)
            map(data["items"], item_iterator)
            Foo()

        """
        logging.debug("Visiting an Expr")
        if isinstance(node.value, ast.Str):
            # This is probably a docstring
            return

        if isinstance(node.value.func, ast.Attribute):
            assert_supported_operation(
                node.value.func.value.id == "data" and node.value.func.attr == "update",
                "The only supported method call is `data.update()` to set values on the input data",
                node,
            )
            state = PassState(
                self.state_graph, f"Pass-{hash_node(node, self.name)}", node
            )
            self._add_state(state)
            self._set_current_state(state)
        elif node.value.func.id == "parallel":
            assert_supported_operation(
                len(node.value.args) > 0,
                "At least one branch function must be provided to the parallel state.",
                node,
            )
            state = ParallelState(self.state_graph, f"Parallel-{hash_node(node)}", node)
            self._add_state(state)
            self._set_current_state(state)
            for arg in node.value.args:
                assert_supported_operation(
                    isinstance(arg, ast.Name)
                    and arg.id in self._state_machine_visitors,
                    "Only defined functions can be provided to the parallel state."
                    f" Available functions: {', '.join(self._other_state_machine_names)}",
                    node,
                )
                state.add_branch(self._state_machine_visitors[arg.id])
                # The referenced state machine is used as a parallel branch so we'll
                # demote it
                self._state_machine_visitors[arg.id].is_first_class = False
        elif node.value.func.id == "wait":
            state = WaitState(self.state_graph, f"Wait-{hash_node(node)}", node)
            self._add_state(state)
            self._set_current_state(state)
        elif node.value.func.id == "map":
            args = node.value.args
            assert_supported_operation(
                len(args) == 2,
                "Map state requires two arguments: a list of items from data and an"
                " iterator function",
                node,
            )
            _, iterator = args
            assert_supported_operation(
                isinstance(iterator, ast.Name)
                and iterator.id in self._state_machine_visitors,
                "Only defined functions can be provided to the map state."
                f" Available functions: {', '.join(self._other_state_machine_names)}",
                node,
            )
            state = MapState(
                self.state_graph,
                f"Map-{hash_node(node)}",
                node,
                self._state_machine_visitors[iterator.id],
            )
            self._add_state(state)
            self._set_current_state(state)
            # The referenced state machine is used as an iterator so we'll demote it
            self._state_machine_visitors[iterator.id].is_first_class = False
            self._state_machine_visitors[iterator.id].is_map_iterator = True
        elif node.value.func.id in self._task_visitors:
            # This node is instantiating a task class
            state = create_task_state(
                self, node, self._task_visitors[node.value.func.id]
            )
            self._add_state(state)
            self._set_current_state(state)
        elif node.value.func.id in self._state_machine_visitors:
            # This node is nesting a state machine
            state = create_task_state(
                self, node, self._state_machine_visitors[node.value.func.id]
            )
            self._add_state(state)
            self._set_current_state(state)
        else:
            raise UnsupportedOperation(
                """Supported expressions include:
* ``update()`` for Pass states
* ``parallel()`` for Parallel states
* ``wait`` for Wait states
* Instantiating Task classes
* Nesting state machines""",
                node,
            )

    def _set_current_state(self, state: State) -> None:
        """Set the current state pointer.

        Args:
            state: New current State

        """
        source = None
        if state is None:
            source = None
        elif hasattr(state.ast_node, "test"):
            source = astor.to_source(state.ast_node.test).strip()
        else:
            source = astor.to_source(state.ast_node).strip()
        logging.debug(f"Setting current state to {state} ({source})")
        self._current_state = state

    def _pop_choice_state_stack(self) -> Optional[ChoiceState]:
        """Pop the last state off the choice state stack and return.

        Returns:
            Instance of ChoiceState or None

        """
        current_choice_state = self._choice_state_stack.pop()
        logging.debug(
            f"Popped current choice state {current_choice_state} from stack (count={len(self._choice_state_stack)})"
        )
        return current_choice_state

    def _push_choice_state_stack(
        self, state: Optional[ChoiceState]
    ) -> Optional[ChoiceState]:
        """Push a new choice state onto the stack and return.

        Returns:
            Instance of ChoiceState or None

        """
        self._choice_state_stack.append(state)
        logging.debug(
            f"Pushed choice state {state} to stack (count={len(self._choice_state_stack)})"
        )
        return state

    def visit_If(self, node: Any) -> None:
        """Visit an if statement

        If statements will have a single if statement, zero or more elif statements,
        and zero or one else statements. In the AST these are recursively nested within
        each node but we need to build a flat list.

        Examples::

            if data["foo"] > 0:
                MyTaskWhenPositive()
            elif data["foo"] < 0:
                MyTaskWhenNegative()
            else:
                MyTaskWhenZero()

        """
        logging.debug("Visiting an If")
        current_choice_state = self._pop_choice_state_stack()

        if isinstance(current_choice_state, ChoiceState) and not self._in_choice_body:
            logging.debug(f"Current ChoiceState is {current_choice_state}")
            choice_branch = current_choice_state.add_choice_branch(node)
            self._set_current_state(choice_branch)
        else:
            logging.debug(
                f"Creating new ChoiceState (_in_choice_body={self._in_choice_body})"
            )
            state = ChoiceState(self.state_graph, f"Choice-{hash_node(node)}", node)
            self._add_state(state)
            self._set_current_state(state.current_choice_branch)
            current_choice_state = self._push_choice_state_stack(state)

        logging.debug("Setting _in_choice_body=true")
        self._in_choice_body = True
        for item in node.body:
            self.visit(item)
        logging.debug("Setting _in_choice_body=false")
        self._in_choice_body = False

        if (len(node.orelse) > 0 and isinstance(node.orelse[0], ast.If)) or len(
            node.orelse
        ) == 0:
            logging.debug("More elif conditions to parse")
            # Append the same state object so we can use it for the next branch
            # of the choice
            current_choice_state = self._push_choice_state_stack(current_choice_state)
        else:
            logging.debug("Parsing final elif choice branch")
            self._set_current_state(current_choice_state)

        logging.debug("Parsing else choice branch")
        self._in_else = True
        assert_supported_operation(
            len(node.orelse) <= 1,
            "A maximum of 1 state can be included in an `else` clause",
            node,
        )
        for item in node.orelse:
            self.visit(item)
        self._in_else = False

        if isinstance(current_choice_state, ChoiceState):
            # This means we're done building the Choice state because otherwise, we'd
            # be adding things to a ChoiceStateBranch. Point the current state back to
            # the Choice object so that it can point to the Next state.
            self._set_current_state(current_choice_state)

    def visit_Raise(self, node: Any) -> None:
        """Visit a raise statement

        Examples::

            raise Exception("Oh no!")
            raise CustomError()

        """
        logging.debug("Visiting a Raise")
        state = FailState(self.state_graph, f"Fail-{hash_node(node)}", node)
        self._add_state(state)
        self._set_current_state(state)

    def visit_Return(self, node: Any) -> None:
        """Visit a return statement

        Returning from the ``main`` function indicates a successful execution.
        """
        logging.debug("Visiting a Return")
        state = SucceedState(
            self.state_graph, f"Succeed-{hash_node(node, self.name)}", node
        )
        self._add_state(state)
        self._set_current_state(state)

    def visit_Try(self, node: Any) -> None:
        """Visit a try statement

        The exception handler nodes are parsed in a different method.

        Examples::

            try:
                MyTask()

        """
        logging.debug("Visiting a Try")
        assert_supported_operation(
            len(node.body) == 1,
            "Only a single task statement at a time can have exception handling applied",
            node,
        )
        assert_supported_operation(
            len(node.orelse) == 0,
            "The `else` part of a try/except block is not currently supported",
            node,
        )
        assert_supported_operation(
            len(node.finalbody) == 0,
            "The `finally` part of a try/except block is not currently supported",
            node,
        )
        assert_supported_operation(
            len(node.handlers) > 0, "At least 1 exception handler is required", node
        )

        for item in node.body:
            self.visit(item)

        for handler in node.handlers:
            self.visit(handler)

        # TODO(jdrake): consider supporting orelse in the future
        # for orelse in node.orelse:
        #     self.visit(orelse)

    def visit_ExceptHandler(self, node: Any) -> None:
        """Visit a exception handler

        The try statement is parsed in a different method.

        Examples:
            except BadThing:
                TaskToHandleBadThing()
            except States.Timeout:
                TaskToPingSlack()

        """
        logging.debug("Visiting an ExceptHandler")
        task = self._current_state
        assert_supported_operation(
            isinstance(task, TaskState),
            "Only task states can have exception handlers",
            node,
        )
        catch = task.add_catch(node)
        self._set_current_state(catch)
        for item in node.body:
            self.visit(item)

        # Repoint the current state at the task so the next ExceptHandler
        # can be appended
        self._set_current_state(task)

    def visit_Pass(self, node: Any) -> None:
        """Visit a pass statement

        A ``pass`` statement should really only be added by the ScriptTransformer as a
        way of filling in missing orelse nodes. The empty Pass state will be used to
        properly link states in the graph and then be removed during the graph shaping
        phase.
        """
        state = PassState(self.state_graph, f"Pass-{hash_node(node, self.name)}", node)
        self._add_state(state)
        self._set_current_state(state)

    def visit_With(self, node: Any) -> None:
        """Visit a with statement

        Only the `retry()` context manager is supported.

        Examples:
            with retry(
                on_exceptions=["CustomError1", CustomError2"],
                interval=10
            ):
                TaskToRetry()

        """
        context_manager = node.items[0].context_expr
        if context_manager.func.id == "retry":
            assert_supported_operation(
                len(node.body) == 1,
                "The retry context manager can only wrap a single task",
                node,
            )
            self.visit(node.body[0])
            task = self._current_state
            task.add_retries(context_manager)
        else:
            raise UnsupportedOperation(
                """Supported context managers include:
* ``retry()`` for retrying tasks
""",
                node,
            )
