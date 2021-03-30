"""Contains class used to represent a Task State that integrates with Step Functions"""
from typing import Dict, Set

from fluxio_parser.states.tasks.base import TaskState


class StateMachineTaskState(TaskState):
    """Task state for executing a nested State Machine.

    This currently only supports the sync invocation pattern.

    See: https://docs.aws.amazon.com/step-functions/latest/dg/connect-stepfunctions.html
    """

    @property
    def resource(self) -> str:
        """Returns the task state Resource key."""
        return "arn:aws:states:::states:startExecution.sync"

    @property
    def parameters(self) -> Dict:
        """Returns the task state Parameters key."""
        return {
            "Input": {
                "AWS_STEP_FUNCTIONS_STARTED_BY_EXECUTION_ID.$": "$$.Execution.Id",
                "__trace.$": "$.__trace",
                "data.$": self._get_input_path(),
            },
            "StateMachineArn": f"${{StateMachine{self.task_definition_name}}}",
        }

    @property
    def variable_names(self) -> Set[str]:
        """Returns set of variable names corresponding to task builder outputs"""
        return {f"StateMachine{self.task_definition_name}"}
