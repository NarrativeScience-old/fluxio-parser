"""Contains class used to represent a Task State that integrates with CodeBuild"""
import json
from typing import Dict, Set

from fluxio_parser.states.tasks.base import TaskState


class CodeBuildTaskState(TaskState):
    """Task state for starting a CodeBuild build

    This currently only supports the sync invocation pattern.

    See: https://docs.aws.amazon.com/step-functions/latest/dg/connect-codebuild.html
    """

    @property
    def resource(self) -> str:
        """Returns the task state Resource key."""
        return "arn:aws:states:::codebuild:startBuild.sync"

    @property
    def parameters(self) -> Dict:
        """Returns the task state Parameters key."""
        parameters = {
            "ProjectName": f"${{CodeBuildProjectName{self.task_definition_name}}}",
            "SourceVersion.$": "$.source_version",
        }
        env = self.options.get("env", {})
        parameters["EnvironmentVariablesOverride"] = [
            {"Name": key, "Value": value} for key, value in env.items()
        ]
        parameters["EnvironmentVariablesOverride"].append(
            {
                "Name": "BUILD_ARG_VARS",
                "Value": json.dumps(self.options.get("build_arg_vars", {})),
            }
        )

        return parameters

    @property
    def variable_names(self) -> Set[str]:
        """Returns set of variable names corresponding to task builder outputs"""
        return {f"CodeBuildProjectName{self.task_definition_name}"}
