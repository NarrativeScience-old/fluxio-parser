"""Contains a class representing a Task State for Lambda via the PEXPM Runner"""
from typing import Dict, Set

from fluxio_parser.states.tasks.base import TaskState
from fluxio_parser.states.tasks.retry import Retry


class LambdaPEXPMRunnerTaskState(TaskState):
    """Task state for Lambda Functions that use the PEXPM Runner.

    This currently only supports the sync invocation pattern.

    See: https://docs.aws.amazon.com/step-functions/latest/dg/connect-lambda.html

    The PEXPM Runner is a generic Lambda function that receives an event payload
    containing metadata about a Python package to execute. It downloads the Python
    package (PEX file) from S3 into /tmp and runs a subprocess. The only reason for
    using the PEXPM Runner instead of building a regular Lambda function is if the
    package artifact is bigger than 250 MB (unpacked) -- PEXPM Runner can handle
    artifacts up to 500 MB.
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
            "package_name": f"${{PackageName{self.task_definition_name}}}",
            "package_version": f"${{PackageVersion{self.task_definition_name}}}",
            "command": [f"${{PackageName{self.task_definition_name}}}", "run"],
            "include_parent_environment": True,
            "return_stdout": True,
            "environment": {
                # Set environment variables using keys from the context object
                # See: https://docs.aws.amazon.com/step-functions/latest/dg/input-output-contextobject.html
                "SFN_EXECUTION_NAME.$": "$$.Execution.Name",
                "SFN_STATE_NAME.$": "$$.State.Name",
                "SFN_STATE_MACHINE_NAME.$": "$$.StateMachine.Name",
                # Pass tracing metadata from the input data object
                "TRACE_ID.$": "$.__trace.id",
                "TRACE_SOURCE.$": "$.__trace.source",
                # Pass the input data
                "SFN_INPUT_VALUE.$": self._get_input_path(),
            },
        }

    @property
    def variable_names(self) -> Set[str]:
        """Returns set of variable names corresponding to task builder outputs"""
        return {
            f"LambdaFunction{self.task_definition_name}",
            f"PackageName{self.task_definition_name}",
            f"PackageVersion{self.task_definition_name}",
        }
