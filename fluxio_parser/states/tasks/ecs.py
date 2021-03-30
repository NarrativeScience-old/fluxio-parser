"""Contains class for a Task State that runs an ECS task"""
from typing import Dict, Set

from fluxio_parser.states.tasks.base import TaskState


class ECSTaskState(TaskState):
    """Task state for ECS tasks.

    This currently only supports the sync pattern.

    See: https://docs.aws.amazon.com/step-functions/latest/dg/connect-ecs.html
    """

    @property
    def resource(self) -> str:
        """Returns the task state Resource key."""
        return "arn:aws:states:::ecs:runTask.sync"

    @property
    def parameters(self) -> Dict:
        """Returns the task state Parameters key."""
        environment = [
            # Set environment variables using keys from the context object
            # See: https://docs.aws.amazon.com/step-functions/latest/dg/input-output-contextobject.html
            {"Name": "SFN_EXECUTION_NAME", "Value.$": "$$.Execution.Name"},
            {"Name": "SFN_STATE_NAME", "Value.$": "$$.State.Name"},
            {"Name": "SFN_STATE_MACHINE_NAME", "Value.$": "$$.StateMachine.Name"},
            # Pass tracing metadata from the input data object
            {"Name": "TRACE_ID", "Value.$": "$.__trace.id"},
            {"Name": "TRACE_SOURCE", "Value.$": "$.__trace.source"},
        ]
        input_path = self._get_input_path()
        if input_path != "$":
            environment.append({"Name": "SFN_INPUT_VALUE", "Value.$": input_path})
        return {
            "LaunchType": "FARGATE",
            "Cluster": "${ECSClusterArn}",
            "TaskDefinition": f"${{ECSTaskDefinition{self.task_definition_name}}}",
            "NetworkConfiguration": {
                "AwsvpcConfiguration": {
                    "AssignPublicIp": "DISABLED",
                    "SecurityGroups": [
                        "${DatabaseSecurityGroup}",
                        "${PrivateLoadBalancerSecurityGroup}",
                    ],
                    "Subnets": ["${Subnet0}", "${Subnet1}", "${Subnet2}", "${Subnet3}"],
                }
            },
            "Overrides": {
                "ContainerOverrides": [
                    {"Name": self.task_definition_name, "Environment": environment}
                ]
            },
        }

    @property
    def variable_names(self) -> Set[str]:
        """Returns set of variable names corresponding to task builder outputs"""
        return {
            "ECSClusterArn",
            f"ECSTaskDefinition{self.task_definition_name}",
            "DatabaseSecurityGroup",
            "PrivateLoadBalancerSecurityGroup",
            "Subnet0",
            "Subnet1",
            "Subnet2",
            "Subnet3",
        }
