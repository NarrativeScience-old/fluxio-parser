"""Contains class used to represent a Task State that integrates with Lambda"""
from typing import Dict, Set

from fluxio_parser.states.tasks.base import TaskState
from fluxio_parser.states.tasks.retry import Retry


class LambdaTaskState(TaskState):
    """Task state for Lambda Functions.

    This currently only supports the sync invocation pattern.

    See: https://docs.aws.amazon.com/step-functions/latest/dg/connect-lambda.html
    """

    DEFAULT_RETRIES = [
        Retry(
            on_exceptions=[
                "Lambda.ServiceException",
                "Lambda.AWSLambdaException",
                "Lambda.SdkClientException",
            ],
            interval=2,
            max_attempts=6,
            backoff_rate=2,
        )
    ]

    @property
    def resource(self) -> str:
        """Returns the task state Resource key."""
        return f"${{LambdaFunction{self.task_definition_name}}}"

    @property
    def parameters(self) -> Dict:
        """Returns the task state Parameters key."""
        return {
            "meta": {
                # Pass metadata using keys from the context object
                # See: https://docs.aws.amazon.com/step-functions/latest/dg/input-output-contextobject.html
                "sfn_execution_name.$": "$$.Execution.Name",
                "sfn_state_name.$": "$$.State.Name",
                "sfn_state_machine_name.$": "$$.StateMachine.Name",
                # Pass tracing metadata from the input data object
                "trace_id.$": "$.__trace.id",
                "trace_source.$": "$.__trace.source",
            },
            "data.$": self._get_input_path(),
        }

    @property
    def variable_names(self) -> Set[str]:
        """Returns set of variable names corresponding to task builder outputs"""
        return {f"LambdaFunction{self.task_definition_name}"}
