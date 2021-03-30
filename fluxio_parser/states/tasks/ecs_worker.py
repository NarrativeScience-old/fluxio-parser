"""Contains class for a Task State that feeds an ECS worker"""
from typing import Dict, Set

from fluxio_parser.states.tasks.base import TaskState


class ECSWorkerTaskState(TaskState):
    """Task state for ECS workers.

    This leverages the waitForTaskToken pattern. The actual task uses the SQS
    integration but it's called "ECS Worker" because an ECS task will read messages from
    the queue and execute the actual task business logic.

    See: https://docs.aws.amazon.com/step-functions/latest/dg/connect-to-resource.html#connect-wait-token
    """

    @property
    def resource(self) -> str:
        """Returns the task state Resource key."""
        return "arn:aws:states:::sqs:sendMessage.waitForTaskToken"

    @property
    def parameters(self) -> Dict:
        """Returns the task state Parameters key."""
        # Construct a message group ID that is unique to the task.
        #
        # Even though we're using a SQS FIFO queue, we don't currently care about
        # the ordering of the items within the execution. Therefore, we'll use a
        # group ID that's unique to the task so we don't inadvertently stall queue
        # processing because of other messages in the execution. From the docs:
        # "When you receive a message with a message group ID, no more messages for
        # the same message group ID are returned unless you delete the message or it
        # becomes visible."
        #
        # The components of the message group ID depend on whether the state is within a
        # map iterator.
        message_group_id = (
            "States.Format('{}_{}_{}', $$.Execution.Name, $$.State.EnteredTime, $.context_index)"
            if self.state_machine_visitor.is_map_iterator
            else "States.Format('{}_{}', $$.Execution.Name, $$.State.EnteredTime)"
        )
        return {
            "QueueUrl": f"${{QueueUrl{self.task_definition_name}}}",
            "MessageGroupId.$": message_group_id,
            "MessageAttributes": {
                "SFN_EXECUTION_NAME": {
                    "DataType": "String",
                    "StringValue.$": "$$.Execution.Name",
                },
                "SFN_STATE_NAME": {
                    "DataType": "String",
                    "StringValue.$": "$$.State.Name",
                },
                "SFN_STATE_MACHINE_NAME": {
                    "DataType": "String",
                    "StringValue.$": "$$.StateMachine.Name",
                },
                # Pass tracing metadata from the input data object
                "TRACE_ID": {"DataType": "String", "StringValue.$": "$.__trace.id"},
                "TRACE_SOURCE": {
                    "DataType": "String",
                    "StringValue.$": "$.__trace.source",
                },
            },
            "MessageBody": {
                "Input.$": self._get_input_path(),
                "TaskToken.$": "$$.Task.Token",
            },
        }

    @property
    def variable_names(self) -> Set[str]:
        """Returns set of variable names corresponding to task builder outputs"""
        return {f"QueueUrl{self.task_definition_name}"}
