"""Unit tests for the Task state"""
import unittest

from .util import StateTestCase


class TestTaskState(StateTestCase):
    """Tests for the Task state"""

    SUCCESSFUL_CASES = [
        (
            "Should include a basic task",
            """
class Action(Task):
    async def run(event, context):
        return

def main(data):
    Action()
""",
            {
                "StartAt": "Action-db6e42286ffe8ccd217c1459c416db7c",
                "States": {
                    "Action-db6e42286ffe8ccd217c1459c416db7c": {
                        "Type": "Task",
                        "Resource": "${LambdaFunctionAction}",
                        "Parameters": {
                            "data.$": "$",
                            "meta": {
                                "sfn_execution_name.$": "$$.Execution.Name",
                                "sfn_state_machine_name.$": "$$.StateMachine.Name",
                                "sfn_state_name.$": "$$.State.Name",
                                "trace_id.$": "$.__trace.id",
                                "trace_source.$": "$.__trace.source",
                            },
                        },
                        "InputPath": "$",
                        "ResultPath": None,
                        "TimeoutSeconds": 300,
                        "End": True,
                        "Retry": [
                            {
                                "ErrorEquals": [
                                    "Lambda.ServiceException",
                                    "Lambda.AWSLambdaException",
                                    "Lambda.SdkClientException",
                                ],
                                "IntervalSeconds": 2,
                                "MaxAttempts": 6,
                                "BackoffRate": 2,
                            }
                        ],
                    }
                },
            },
        ),
        (
            "Should set lambda service",
            """
class Action(Task):
    service = "lambda"
    async def run(event, context):
        return

def main(data):
    Action()
""",
            {
                "StartAt": "Action-db6e42286ffe8ccd217c1459c416db7c",
                "States": {
                    "Action-db6e42286ffe8ccd217c1459c416db7c": {
                        "Type": "Task",
                        "Resource": "${LambdaFunctionAction}",
                        "Parameters": {
                            "data.$": "$",
                            "meta": {
                                "sfn_execution_name.$": "$$.Execution.Name",
                                "sfn_state_machine_name.$": "$$.StateMachine.Name",
                                "sfn_state_name.$": "$$.State.Name",
                                "trace_id.$": "$.__trace.id",
                                "trace_source.$": "$.__trace.source",
                            },
                        },
                        "InputPath": "$",
                        "ResultPath": None,
                        "TimeoutSeconds": 300,
                        "End": True,
                        "Retry": [
                            {
                                "ErrorEquals": [
                                    "Lambda.ServiceException",
                                    "Lambda.AWSLambdaException",
                                    "Lambda.SdkClientException",
                                ],
                                "IntervalSeconds": 2,
                                "MaxAttempts": 6,
                                "BackoffRate": 2,
                            }
                        ],
                    }
                },
            },
        ),
        (
            "Should set lambda:pexpm-runner service",
            """
class Action(Task):
    service = "lambda:pexpm-runner"
    async def run(event, context):
        return

def main(data):
    Action(key="action")
""",
            {
                "StartAt": "action",
                "States": {
                    "action": {
                        "Type": "Task",
                        "Resource": "${LambdaFunctionAction}",
                        "Parameters": {
                            "package_name": "${PackageNameAction}",
                            "package_version": "${PackageVersionAction}",
                            "command": ["${PackageNameAction}", "run"],
                            "include_parent_environment": True,
                            "return_stdout": True,
                            "environment": {
                                "SFN_EXECUTION_NAME.$": "$$.Execution.Name",
                                "SFN_STATE_NAME.$": "$$.State.Name",
                                "SFN_STATE_MACHINE_NAME.$": "$$.StateMachine.Name",
                                "TRACE_ID.$": "$.__trace.id",
                                "TRACE_SOURCE.$": "$.__trace.source",
                                "SFN_INPUT_VALUE.$": "$",
                            },
                        },
                        "InputPath": "$",
                        "ResultPath": None,
                        "TimeoutSeconds": 300,
                        "End": True,
                        "Retry": [
                            {
                                "ErrorEquals": [
                                    "Lambda.ServiceException",
                                    "Lambda.AWSLambdaException",
                                    "Lambda.SdkClientException",
                                ],
                                "IntervalSeconds": 2,
                                "MaxAttempts": 6,
                                "BackoffRate": 2,
                            }
                        ],
                    }
                },
            },
        ),
        (
            "Should set ecs service",
            """
class Action(Task):
    service = "ecs"
    async def run(event, context):
        return

def main(data):
    Action()
""",
            {
                "StartAt": "Action-db6e42286ffe8ccd217c1459c416db7c",
                "States": {
                    "Action-db6e42286ffe8ccd217c1459c416db7c": {
                        "Type": "Task",
                        "Resource": "arn:aws:states:::ecs:runTask.sync",
                        "Parameters": {
                            "LaunchType": "FARGATE",
                            "Cluster": "${ECSClusterArn}",
                            "TaskDefinition": "${ECSTaskDefinitionAction}",
                            "NetworkConfiguration": {
                                "AwsvpcConfiguration": {
                                    "AssignPublicIp": "DISABLED",
                                    "SecurityGroups": [
                                        "${DatabaseSecurityGroup}",
                                        "${PrivateLoadBalancerSecurityGroup}",
                                    ],
                                    "Subnets": [
                                        "${Subnet0}",
                                        "${Subnet1}",
                                        "${Subnet2}",
                                        "${Subnet3}",
                                    ],
                                }
                            },
                            "Overrides": {
                                "ContainerOverrides": [
                                    {
                                        "Name": "Action",
                                        "Environment": [
                                            {
                                                "Name": "SFN_EXECUTION_NAME",
                                                "Value.$": "$$.Execution.Name",
                                            },
                                            {
                                                "Name": "SFN_STATE_NAME",
                                                "Value.$": "$$.State.Name",
                                            },
                                            {
                                                "Name": "SFN_STATE_MACHINE_NAME",
                                                "Value.$": "$$.StateMachine.Name",
                                            },
                                            {
                                                "Name": "TRACE_ID",
                                                "Value.$": "$.__trace.id",
                                            },
                                            {
                                                "Name": "TRACE_SOURCE",
                                                "Value.$": "$.__trace.source",
                                            },
                                        ],
                                    }
                                ]
                            },
                        },
                        "InputPath": "$",
                        "ResultPath": None,
                        "TimeoutSeconds": 300,
                        "End": True,
                    }
                },
            },
        ),
        (
            "Should set ecs:worker service",
            """
class Action(Task):
    service = "ecs:worker"
    async def run(event, context):
        return

def main(data):
    Action()
""",
            {
                "StartAt": "Action-db6e42286ffe8ccd217c1459c416db7c",
                "States": {
                    "Action-db6e42286ffe8ccd217c1459c416db7c": {
                        "Type": "Task",
                        "Resource": "arn:aws:states:::sqs:sendMessage.waitForTaskToken",
                        "Parameters": {
                            "QueueUrl": "${QueueUrlAction}",
                            "MessageGroupId.$": "States.Format('{}_{}', $$.Execution.Name, $$.State.EnteredTime)",
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
                                "TRACE_ID": {
                                    "DataType": "String",
                                    "StringValue.$": "$.__trace.id",
                                },
                                "TRACE_SOURCE": {
                                    "DataType": "String",
                                    "StringValue.$": "$.__trace.source",
                                },
                            },
                            "MessageBody": {
                                "Input.$": "$",
                                "TaskToken.$": "$$.Task.Token",
                            },
                        },
                        "InputPath": "$",
                        "ResultPath": None,
                        "TimeoutSeconds": 300,
                        "End": True,
                    }
                },
            },
        ),
        (
            "Should accept key option",
            """
class Action(Task):
    async def run(event, context):
        return

def main(data):
    Action(key="action")
""",
            {
                "StartAt": "action",
                "States": {
                    "action": {
                        "Type": "Task",
                        "Resource": "${LambdaFunctionAction}",
                        "Parameters": {
                            "data.$": "$",
                            "meta": {
                                "sfn_execution_name.$": "$$.Execution.Name",
                                "sfn_state_machine_name.$": "$$.StateMachine.Name",
                                "sfn_state_name.$": "$$.State.Name",
                                "trace_id.$": "$.__trace.id",
                                "trace_source.$": "$.__trace.source",
                            },
                        },
                        "InputPath": "$",
                        "ResultPath": None,
                        "TimeoutSeconds": 300,
                        "End": True,
                        "Retry": [
                            {
                                "ErrorEquals": [
                                    "Lambda.ServiceException",
                                    "Lambda.AWSLambdaException",
                                    "Lambda.SdkClientException",
                                ],
                                "IntervalSeconds": 2,
                                "MaxAttempts": 6,
                                "BackoffRate": 2,
                            }
                        ],
                    }
                },
            },
        ),
        (
            "Should accept timeout option",
            """
class Action(Task):
    async def run(event, context):
        return

def main(data):
    Action(key="action", timeout=10)
""",
            {
                "StartAt": "action",
                "States": {
                    "action": {
                        "Type": "Task",
                        "Resource": "${LambdaFunctionAction}",
                        "Parameters": {
                            "data.$": "$",
                            "meta": {
                                "sfn_execution_name.$": "$$.Execution.Name",
                                "sfn_state_machine_name.$": "$$.StateMachine.Name",
                                "sfn_state_name.$": "$$.State.Name",
                                "trace_id.$": "$.__trace.id",
                                "trace_source.$": "$.__trace.source",
                            },
                        },
                        "InputPath": "$",
                        "ResultPath": None,
                        "TimeoutSeconds": 10,
                        "End": True,
                        "Retry": [
                            {
                                "ErrorEquals": [
                                    "Lambda.ServiceException",
                                    "Lambda.AWSLambdaException",
                                    "Lambda.SdkClientException",
                                ],
                                "IntervalSeconds": 2,
                                "MaxAttempts": 6,
                                "BackoffRate": 2,
                            }
                        ],
                    }
                },
            },
        ),
        (
            "Should accept input data",
            """
class Action(Task):
    async def run(event, context):
        return

def main(data):
    Action(data["input"], key="action")
""",
            {
                "StartAt": "action",
                "States": {
                    "action": {
                        "Type": "Task",
                        "Resource": "${LambdaFunctionAction}",
                        "Parameters": {
                            "data.$": "$['input']",
                            "meta": {
                                "sfn_execution_name.$": "$$.Execution.Name",
                                "sfn_state_machine_name.$": "$$.StateMachine.Name",
                                "sfn_state_name.$": "$$.State.Name",
                                "trace_id.$": "$.__trace.id",
                                "trace_source.$": "$.__trace.source",
                            },
                        },
                        "InputPath": "$",
                        "ResultPath": None,
                        "TimeoutSeconds": 300,
                        "End": True,
                        "Retry": [
                            {
                                "ErrorEquals": [
                                    "Lambda.ServiceException",
                                    "Lambda.AWSLambdaException",
                                    "Lambda.SdkClientException",
                                ],
                                "IntervalSeconds": 2,
                                "MaxAttempts": 6,
                                "BackoffRate": 2,
                            }
                        ],
                    }
                },
            },
        ),
        (
            "Should set result path",
            """
class Action(Task):
    async def run(event, context):
        return

def main(data):
    data["output"] = Action(data["input"], key="action")
""",
            {
                "StartAt": "action",
                "States": {
                    "action": {
                        "Type": "Task",
                        "Resource": "${LambdaFunctionAction}",
                        "Parameters": {
                            "data.$": "$['input']",
                            "meta": {
                                "sfn_execution_name.$": "$$.Execution.Name",
                                "sfn_state_machine_name.$": "$$.StateMachine.Name",
                                "sfn_state_name.$": "$$.State.Name",
                                "trace_id.$": "$.__trace.id",
                                "trace_source.$": "$.__trace.source",
                            },
                        },
                        "InputPath": "$",
                        "ResultPath": "$['output']",
                        "TimeoutSeconds": 300,
                        "End": True,
                        "Retry": [
                            {
                                "ErrorEquals": [
                                    "Lambda.ServiceException",
                                    "Lambda.AWSLambdaException",
                                    "Lambda.SdkClientException",
                                ],
                                "IntervalSeconds": 2,
                                "MaxAttempts": 6,
                                "BackoffRate": 2,
                            }
                        ],
                    }
                },
            },
        ),
        (
            "Should include nested state machine",
            """
def nested(data):
    return

def main(data):
    nested(key="nested")
""",
            {
                "StartAt": "nested",
                "States": {
                    "nested": {
                        "Type": "Task",
                        "Resource": "arn:aws:states:::states:startExecution.sync",
                        "Parameters": {
                            "Input": {
                                "AWS_STEP_FUNCTIONS_STARTED_BY_EXECUTION_ID.$": "$$.Execution.Id",
                                "__trace.$": "$.__trace",
                                "data.$": "$",
                            },
                            "StateMachineArn": "${StateMachinenested}",
                        },
                        "InputPath": "$",
                        "ResultPath": None,
                        "TimeoutSeconds": 300,
                        "End": True,
                    }
                },
            },
        ),
        (
            "Should catch unnamed exception",
            """
class Action(Task):
    async def run(event, context):
        return

def main(data):
    try:
        Action(key="action")
    except:
        return
""",
            {
                "StartAt": "action",
                "States": {
                    "action": {
                        "Type": "Task",
                        "Resource": "${LambdaFunctionAction}",
                        "Parameters": {
                            "data.$": "$",
                            "meta": {
                                "sfn_execution_name.$": "$$.Execution.Name",
                                "sfn_state_machine_name.$": "$$.StateMachine.Name",
                                "sfn_state_name.$": "$$.State.Name",
                                "trace_id.$": "$.__trace.id",
                                "trace_source.$": "$.__trace.source",
                            },
                        },
                        "InputPath": "$",
                        "ResultPath": None,
                        "TimeoutSeconds": 300,
                        "End": True,
                        "Catch": [
                            {
                                "ErrorEquals": ["States.ALL"],
                                "ResultPath": "$.error",
                                "Next": "Succeed-d1d0f861f06db686c59bfded9f95b5c4",
                            }
                        ],
                        "Retry": [
                            {
                                "ErrorEquals": [
                                    "Lambda.ServiceException",
                                    "Lambda.AWSLambdaException",
                                    "Lambda.SdkClientException",
                                ],
                                "IntervalSeconds": 2,
                                "MaxAttempts": 6,
                                "BackoffRate": 2,
                            }
                        ],
                    },
                    "Succeed-d1d0f861f06db686c59bfded9f95b5c4": {"Type": "Succeed"},
                },
            },
        ),
        (
            "Should catch base exception",
            """
class Action(Task):
    async def run(event, context):
        return

def main(data):
    try:
        Action(key="action")
    except Exception:
        return
""",
            {
                "StartAt": "action",
                "States": {
                    "action": {
                        "Type": "Task",
                        "Resource": "${LambdaFunctionAction}",
                        "Parameters": {
                            "data.$": "$",
                            "meta": {
                                "sfn_execution_name.$": "$$.Execution.Name",
                                "sfn_state_machine_name.$": "$$.StateMachine.Name",
                                "sfn_state_name.$": "$$.State.Name",
                                "trace_id.$": "$.__trace.id",
                                "trace_source.$": "$.__trace.source",
                            },
                        },
                        "InputPath": "$",
                        "ResultPath": None,
                        "TimeoutSeconds": 300,
                        "End": True,
                        "Catch": [
                            {
                                "ErrorEquals": ["Exception"],
                                "ResultPath": "$.error",
                                "Next": "Succeed-d1d0f861f06db686c59bfded9f95b5c4",
                            }
                        ],
                        "Retry": [
                            {
                                "ErrorEquals": [
                                    "Lambda.ServiceException",
                                    "Lambda.AWSLambdaException",
                                    "Lambda.SdkClientException",
                                ],
                                "IntervalSeconds": 2,
                                "MaxAttempts": 6,
                                "BackoffRate": 2,
                            }
                        ],
                    },
                    "Succeed-d1d0f861f06db686c59bfded9f95b5c4": {"Type": "Succeed"},
                },
            },
        ),
        (
            "Should catch custom exception",
            """
class Action(Task):
    async def run(event, context):
        return

def main(data):
    try:
        Action(key="action")
    except CustomError:
        return
""",
            {
                "StartAt": "action",
                "States": {
                    "action": {
                        "Type": "Task",
                        "Resource": "${LambdaFunctionAction}",
                        "Parameters": {
                            "data.$": "$",
                            "meta": {
                                "sfn_execution_name.$": "$$.Execution.Name",
                                "sfn_state_machine_name.$": "$$.StateMachine.Name",
                                "sfn_state_name.$": "$$.State.Name",
                                "trace_id.$": "$.__trace.id",
                                "trace_source.$": "$.__trace.source",
                            },
                        },
                        "InputPath": "$",
                        "ResultPath": None,
                        "TimeoutSeconds": 300,
                        "End": True,
                        "Catch": [
                            {
                                "ErrorEquals": ["CustomError"],
                                "ResultPath": "$.error",
                                "Next": "Succeed-d1d0f861f06db686c59bfded9f95b5c4",
                            }
                        ],
                        "Retry": [
                            {
                                "ErrorEquals": [
                                    "Lambda.ServiceException",
                                    "Lambda.AWSLambdaException",
                                    "Lambda.SdkClientException",
                                ],
                                "IntervalSeconds": 2,
                                "MaxAttempts": 6,
                                "BackoffRate": 2,
                            }
                        ],
                    },
                    "Succeed-d1d0f861f06db686c59bfded9f95b5c4": {"Type": "Succeed"},
                },
            },
        ),
        (
            "Should catch multiple exceptions in a single handler",
            """
class Action(Task):
    async def run(event, context):
        return

def main(data):
    try:
        Action(key="action")
    except (CustomError1, CustomError2):
        return
""",
            {
                "StartAt": "action",
                "States": {
                    "action": {
                        "Type": "Task",
                        "Resource": "${LambdaFunctionAction}",
                        "Parameters": {
                            "data.$": "$",
                            "meta": {
                                "sfn_execution_name.$": "$$.Execution.Name",
                                "sfn_state_machine_name.$": "$$.StateMachine.Name",
                                "sfn_state_name.$": "$$.State.Name",
                                "trace_id.$": "$.__trace.id",
                                "trace_source.$": "$.__trace.source",
                            },
                        },
                        "InputPath": "$",
                        "ResultPath": None,
                        "TimeoutSeconds": 300,
                        "End": True,
                        "Catch": [
                            {
                                "ErrorEquals": ["CustomError1", "CustomError2"],
                                "ResultPath": "$.error",
                                "Next": "Succeed-d1d0f861f06db686c59bfded9f95b5c4",
                            }
                        ],
                        "Retry": [
                            {
                                "ErrorEquals": [
                                    "Lambda.ServiceException",
                                    "Lambda.AWSLambdaException",
                                    "Lambda.SdkClientException",
                                ],
                                "IntervalSeconds": 2,
                                "MaxAttempts": 6,
                                "BackoffRate": 2,
                            }
                        ],
                    },
                    "Succeed-d1d0f861f06db686c59bfded9f95b5c4": {"Type": "Succeed"},
                },
            },
        ),
        (
            "Should parse multiple exception handlers",
            """
class Action(Task):
    async def run(event, context):
        return

def main(data):
    try:
        Action(key="action")
    except CustomError1:
        return
    except CustomError2:
        return
""",
            {
                "StartAt": "action",
                "States": {
                    "action": {
                        "Type": "Task",
                        "Resource": "${LambdaFunctionAction}",
                        "Parameters": {
                            "data.$": "$",
                            "meta": {
                                "sfn_execution_name.$": "$$.Execution.Name",
                                "sfn_state_machine_name.$": "$$.StateMachine.Name",
                                "sfn_state_name.$": "$$.State.Name",
                                "trace_id.$": "$.__trace.id",
                                "trace_source.$": "$.__trace.source",
                            },
                        },
                        "InputPath": "$",
                        "ResultPath": None,
                        "TimeoutSeconds": 300,
                        "End": True,
                        "Catch": [
                            {
                                "ErrorEquals": ["CustomError1"],
                                "ResultPath": "$.error",
                                "Next": "Succeed-d1d0f861f06db686c59bfded9f95b5c4",
                            },
                            {
                                "ErrorEquals": ["CustomError2"],
                                "ResultPath": "$.error",
                                "Next": "Succeed-d1d0f861f06db686c59bfded9f95b5c4",
                            },
                        ],
                        "Retry": [
                            {
                                "ErrorEquals": [
                                    "Lambda.ServiceException",
                                    "Lambda.AWSLambdaException",
                                    "Lambda.SdkClientException",
                                ],
                                "IntervalSeconds": 2,
                                "MaxAttempts": 6,
                                "BackoffRate": 2,
                            }
                        ],
                    },
                    "Succeed-d1d0f861f06db686c59bfded9f95b5c4": {"Type": "Succeed"},
                },
            },
        ),
        (
            "Should add retry to the task",
            """
class Action(Task):
    async def run(event, context):
        return

def main(data):
    with retry(
        on_exceptions=[CustomError, States.TaskFailed],
        interval=10,
        max_attempts=5,
        backoff_rate=3.0
    ):
        Action()
""",
            {
                "StartAt": "Action-db6e42286ffe8ccd217c1459c416db7c",
                "States": {
                    "Action-db6e42286ffe8ccd217c1459c416db7c": {
                        "Type": "Task",
                        "Resource": "${LambdaFunctionAction}",
                        "Parameters": {
                            "data.$": "$",
                            "meta": {
                                "sfn_execution_name.$": "$$.Execution.Name",
                                "sfn_state_machine_name.$": "$$.StateMachine.Name",
                                "sfn_state_name.$": "$$.State.Name",
                                "trace_id.$": "$.__trace.id",
                                "trace_source.$": "$.__trace.source",
                            },
                        },
                        "InputPath": "$",
                        "ResultPath": None,
                        "TimeoutSeconds": 300,
                        "End": True,
                        "Retry": [
                            {
                                "ErrorEquals": [
                                    "Lambda.ServiceException",
                                    "Lambda.AWSLambdaException",
                                    "Lambda.SdkClientException",
                                ],
                                "IntervalSeconds": 2,
                                "MaxAttempts": 6,
                                "BackoffRate": 2,
                            },
                            {
                                "ErrorEquals": ["CustomError", "States.TaskFailed"],
                                "IntervalSeconds": 10,
                                "MaxAttempts": 5,
                                "BackoffRate": 3.0,
                            },
                        ],
                    }
                },
            },
        ),
        (
            "Should add retry to the task with default values",
            """
class Action(Task):
    async def run(event, context):
        return

def main(data):
    with retry():
        Action()
""",
            {
                "StartAt": "Action-db6e42286ffe8ccd217c1459c416db7c",
                "States": {
                    "Action-db6e42286ffe8ccd217c1459c416db7c": {
                        "Type": "Task",
                        "Resource": "${LambdaFunctionAction}",
                        "Parameters": {
                            "data.$": "$",
                            "meta": {
                                "sfn_execution_name.$": "$$.Execution.Name",
                                "sfn_state_machine_name.$": "$$.StateMachine.Name",
                                "sfn_state_name.$": "$$.State.Name",
                                "trace_id.$": "$.__trace.id",
                                "trace_source.$": "$.__trace.source",
                            },
                        },
                        "InputPath": "$",
                        "ResultPath": None,
                        "TimeoutSeconds": 300,
                        "End": True,
                        "Retry": [
                            {
                                "ErrorEquals": [
                                    "Lambda.ServiceException",
                                    "Lambda.AWSLambdaException",
                                    "Lambda.SdkClientException",
                                ],
                                "IntervalSeconds": 2,
                                "MaxAttempts": 6,
                                "BackoffRate": 2,
                            },
                            {
                                "ErrorEquals": ["Exception"],
                                "IntervalSeconds": 1,
                                "MaxAttempts": 3,
                                "BackoffRate": 2.0,
                            },
                        ],
                    }
                },
            },
        ),
    ]

    UNSUPPORTED_CASES = [
        (
            "Should raise if unknown task class",
            """
class Action(Task):
    async def run(event, context):
        return

def main(data):
    Unknown()
""",
            "Supported expressions",
        ),
        (
            "Should raise if invalid key option",
            """
class Action(Task):
    async def run(event, context):
        return

def main(data):
    Action(key=123)
""",
            "key",
        ),
        (
            "Should raise if invalid timeout option",
            """
class Action(Task):
    async def run(event, context):
        return

def main(data):
    Action(timeout="10")
""",
            "timeout",
        ),
        (
            "Should raise if invalid result path",
            """
class Action(Task):
    async def run(event, context):
        return

def main(data):
    data["__trace"] = Action(key="action")
""",
            "reserved",
        ),
        (
            "Should raise if multiple tasks in try body",
            """
class Action(Task):
    async def run(event, context):
        return

def main(data):
    try:
        Action()
        Action()
    except:
        return
""",
            "single task statement",
        ),
        (
            "Should raise if else used with try",
            """
class Action(Task):
    async def run(event, context):
        return

def main(data):
    try:
        Action()
    except:
        return
    else:
        return
""",
            "`else` part",
        ),
        (
            "Should raise if finally used with try",
            """
class Action(Task):
    async def run(event, context):
        return

def main(data):
    try:
        Action()
    finally:
        return
""",
            "`finally` part",
        ),
        (
            "Should raise if invalid service",
            """
class Action(Task):
    service = "ec2"
    async def run(event, context):
        return

def main(data):
    Action()
""",
            "service",
        ),
        (
            "Should raise if multiple tasks in retry block",
            """
class Action(Task):
    async def run(event, context):
        return

def main(data):
    with retry():
        Action()
        Action()
""",
            "single task",
        ),
        (
            "Should raise if unsupported context manager in with block",
            """
class Action(Task):
    async def run(event, context):
        return

def main(data):
    with open():
        Action()
""",
            "context manager",
        ),
    ]


if __name__ == "__main__":
    unittest.main()
