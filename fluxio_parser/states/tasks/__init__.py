"""Contains a factory function for creating new Task state instances"""
from typing import Any, Union

from fluxio_parser.states.tasks.base import OPTION_MAP
from fluxio_parser.states.tasks.codebuild import CodeBuildTaskState
from fluxio_parser.states.tasks.ecs import ECSTaskState
from fluxio_parser.states.tasks.ecs_worker import ECSWorkerTaskState
from fluxio_parser.states.tasks.lambda_function import LambdaTaskState
from fluxio_parser.states.tasks.lambda_pexpm_runner import LambdaPEXPMRunnerTaskState
from fluxio_parser.states.tasks.state_machine import StateMachineTaskState
from fluxio_parser.util import parse_options

#: Map of service key to task state class
TASK_STATE_MAP = {
    "codebuild": CodeBuildTaskState,
    "ecs": ECSTaskState,
    "ecs:worker": ECSWorkerTaskState,
    "lambda": LambdaTaskState,
    "lambda:container": LambdaTaskState,
    "lambda:pexpm-runner": LambdaPEXPMRunnerTaskState,
    "state-machine": StateMachineTaskState,
}


def create_task_state(
    state_machine_visitor: "StateMachineVisitor",
    ast_node: Any,
    visitor: Union["TaskVisitor", "StateMachineVisitor"],
):
    """Factory function to create a new task state instance.

    Args:
        state_machine_visitor: State machine visitor that is the parent of this new state
        ast_node: AST node for this fragment in the .sfn file
        visitor: Instance of a task or state machine visitor. This is used to parse
            options.

    Returns:
        new task state

    """
    service = visitor.attributes.get("service", "lambda")
    options = {}
    # Start with the options defined on the task class attributes
    options.update(visitor.attributes)
    # Override using the options passed to this task node
    options.update(parse_options(OPTION_MAP, ast_node.value))
    return TASK_STATE_MAP[service](
        state_machine_visitor.state_graph,
        options["key"],
        ast_node,
        state_machine_visitor,
        options,
    )
