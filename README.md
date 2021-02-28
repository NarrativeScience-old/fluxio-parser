# Fluxio Parser

Fluxio is a framework for building workflows using Python. This is the parser component. Its job is to parse a Fluxio project's Python DSL into an in-memory representation. Other components translate the parsed project into deployable artifacts.

- [Fluxio DSL](#fluxio-dsl)
- [Input Data](#input-data)
- [States](#states)
- [Task](#task)
  - [Definition](#definition)
  - [Adding to the state machine](#adding-to-the-state-machine)
  - [Passing data to tasks](#passing-data-to-tasks)
  - [Stopping the execution](#stopping-the-execution)
  - [Working with the State Data Client](#working-with-the-state-data-client)
  - [Error Handling](#error-handling)
  - [Retries](#retries)
  - [Choice](#choice)
  - [Map](#map)
  - [Parallel](#parallel)
  - [Pass](#pass)
  - [Succeed](#succeed)
  - [Fail](#fail)
  - [Wait](#wait)
- [Decorators](#decorators)
  - [schedule](#schedule)
  - [subscribe](#subscribe)
  - [export](#export)

## Fluxio DSL

Fluxio employs a [DSL](https://en.wikipedia.org/wiki/Domain-specific_language) written in Python syntax; this means a file's [abstract syntax tree (AST)](https://docs.python.org/3/library/ast.html) is parsed from source code instead of the module being executed directly by the Python interpreter.

An Fluxio project file contains:

- A module-level function named "main" that defines the state machine logic. This function will be parsed later transpiled to [Amazon States Language (ASL)](https://docs.aws.amazon.com/step-functions/latest/dg/concepts-amazon-states-language.html).
  - The function should define a single positional arg, data, for explicitness but technically it doesn't matter. This variable represents the input data to the state machine execution, referenced as $ in ASL.
  - See the [States](#states) section below for how to define the various states in Fluxio syntax
- If the state machine needs any task states, then one or more module-level classes should be defined.
  - Each class must have a unique, PascalCased name.
    - Each class must inherit from [`Task`](#task).
    - Each class should define a `run` method that takes the following positional arguments:
      - `event` will be the input data
      - `context` contains clients, functions, and attributes related to task metadata

## [Input Data](https://docs.aws.amazon.com/step-functions/latest/dg/concepts-input-output-filtering.html)

Within the main function, the data variable is the state input and is referenced as $ in ASL. We used it to pass parameters into and store data resulting from Task states. You can also set static values or transform the input data with a Pass state. The data variable is a dictionary.

## States

The `states` subpackage has modules that roughly correspond to the actual state machine states. There is a base class called `StateMachineFragment` that represents some chunk of the state machine. The base `State` class only really exists to provide a more conceptually readable parent to the various subclasses in the states subpackage. State machine fragments that are not states include `ChoiceBranch`, parallel's `Branch`, and task's `Catch`.

The `tasks` subpackage within `states` contains different types of task states that resolve differently depending on the service specified in the Fluxio file. We have a task state that works with sync Lambda Functions and sync ECS tasks. A factory function in the subpackage's `__init__.py` determines the relevant task state class.

The following subsections explain how to represent a given ASL State in a Fluxio file. Click on each section heading to learn about each state's purpose.

## [Task](https://docs.aws.amazon.com/step-functions/latest/dg/amazon-states-language-task-state.html)

### Definition

To define a task, add a Task subclass with a run method:

```python
class Bar(Task):
    async def run(event, context):
        event.update({"bar": 456})
        return event
```

#### `run` method

The run method should be async for consistency. The Lambda/ECS entry point code will get the current event loop and run the method.

The run method will be extracted **as-is** and used to replace a module in the generated Python package before the package is built for deployment. This means any import statements should go in the body of this method. You can include any application code you want. However, if your run method is more than ~50 LOC, you should probably create a separate library package then import and execute it in the run method.

The `ecs:worker` service type does not use the `run` method.

#### `service` attribute

By default, the task will be deployed as a Lambda Function. To explicitly set the service (the runtime of the task), add a class attribute:

```python
class Bar(Task):
    service = "ecs"
    async def run(event, context):
        from ns_ml_runtime_thing import do_ml

        do_ml(event)
```

Options currently include:

- `lambda`
- `ecs`
- `lambda:pexpm-runner`
  - __NOTE:__ PEXPM Runner is a Lambda function that downloads a PEX binary to /tmp and executes it in a subprocess at runtime. This should only be used to get around the 250MB artifact limit.
- `ecs:worker`
  - See below for specifics

##### ECS Worker

The `ecs:worker` service type uses the ["Wait for Task Token" service integration pattern in Step Functions](https://docs.aws.amazon.com/step-functions/latest/dg/connect-to-resource.html#connect-wait-token). This means instead of directly running a task, like a Lambda Function or ECS task, a message is sent to an SQS queue for processing by an external system. In Fluxio, the external system is an ECS Fargate service. The tasks in the service are queue workers; they poll the SQS queue and execute business logic based on the message. All the SQS and ECS infrastructure is managed by Fluxio (via CloudFormation) just like other service types.

This service type is a good fit if your use case:

- Needs to use ECS: maybe your package artifact size is too big for Lambda or you need to run a task for longer than 15 minutes
- Exceeds the [maximum number of tasks that can be launched per RunTask API action](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-quotas.html)

The ECS worker pattern allows to run one or more workers in the background to support long-running tasks as well as limit the number of API requests that Step Functions makes to ECS.

To get started, first extend the `TaskWorker` class and put your code in a regular package. For example, we'll define a new class called `TestWorker` in the `ns_worker_test` package in the `worker.py` module:

```python
"""Contains TestWorker class"""

import logging
from typing import Dict

import aioredis

from ns_sfn_task_entry_points.ecs_worker_app import TaskContext, TaskWorker

logger = logging.getLogger()


class TestWorker(TaskWorker):
    """Test worker"""

    async def on_startup(self):
        """Initialize global application state"""
        await super().on_startup()
        self.cache_client_engine = await aioredis.create_redis_pool(...)

    async def on_cleanup(self) -> None:
        """Tear down the worker context"""
        await super().on_cleanup()
        self.cache_client_engine.close()
        await self.cache_client_engine.wait_closed()

    async def run(self, event: Dict, context: TaskContext):
        """Run the task, i.e. handle a single queue message

        This method exists for compatibility with other Fluxio tasks.

        Args:
            event: Event/input data unpacked from the queue message
            context: Task context object containing clients, functions, and metadata

        """
        item = context.state_data_client.get_item_for_map_iteration(event)
        logger.info(item)
```

Note that you can define `on_startup` and `on_cleanup` lifecycle methods. These allow you to create database engines and API clients once when the application launches instead of with every message.

Next, define a Task in your `project.py` file and at least the `spec` attribute:

```python
class GenerateItems(Task):
    async def run(event, context):
        return context.state_data_client.put_items(
            "items",
            [{"name": "sue"}, {"name": "jae"}, {"name": "levi"}]
        )

class Worker(Task):
    service = "ecs:worker"
    spec = "ns_worker_test.worker:TestWorker"
    timeout = 600
    concurrency = 10
    heartbeat_interval = 60
    autoscaling_min = 1
    autoscaling_max = 2

def process_item(data):
    Worker()

def main(data):
    data["items"] = GenerateItems()
    map(data["items"], process_item)
```

Available attributes:

- `spec`: reference the path to your new class in the format `package.module:Class`
- `concurrency` (default: 1): maximum number of messages to concurrently process within each task. Value must be in range 1-100. If the message handler does CPU-intensive work, this should be set to 1. The memory/CPU allotted to the task will determine how high this number can go. For I/O-intensive work, this number can generally be set to 10 per GB of memory but your mileage may vary.
- `heartbeat_interval` (default: None): interval in seconds between heartbeat events sent to SQS. This value must be below the task timeout value. If the value is None, the task will not send heartbeats and the message timeout will default to the queue's timeout. A heartbeat "resets the clock" on an individual message's visibility timeout. Once a heartbeat happens, then the message will become visible in `<interval> * 2` seconds unless another heartbeat occurs in `<interval>` seconds. If the task stops (like during a deployment), the timeout will expire and another task can receive the message. See the docs at [Amazon SQS visibility timeout
](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html) for more details.
- `autoscaling_min` (default: 1): minimum number of ECS tasks. Setting this to 1 means the service will always run at least one worker
- `autoscaling_max` (default: 1): maximum number of ECS tasks

#### `timeout` attribute

By default the task will timeout after 300 seconds. To change that value, set a class attribute:

```python
class Bar(Task):
    timeout = 600  # 10 minutes
    async def run(event, context):
        # ...
```

You also need to provide that new timeout value as a keyword argument when you use the task:

```python
def main(data):
    Bar(key="Bar", timeout=600)
```

#### `cpu` and `memory` attributes

The `memory` attribute is only used by Lambda and ECS tasks. The `cpu` attribute is only used by ECS tasks.

By default the `cpu` is set to 1024 and the `memory` is set to 2048. To change those values, set class attributes:

```python
class Bar(Task):
    cpu = 2048  # 2 vCPU
    memory = 4096  # 4 GB
    async def run(event, context):
        # ...
```

For ECS:

- The available CPU values are 256, 512, 1024, 2048, 4096
- The memory value is tied to the CPU but should generally be set to at least 2 times greater than the CPU value

For Lambda:

- The available memory values are 128, 512, 1024, 1536, 2048, 3008

### Adding to the state machine

To add a Task state, instantiate the Task class within the main function. You can either:

- Instantiate the class and assign the result to a key in the input data (recommended).
  - This is supported for services that can return a result from the task. Only Lambda can do this. This means that returning a result in the run method will not do anything if the service is set to "ecs".
- Instantiate the class and do not assign its result.
  - This means that the result of the task will be discarded, i.e. it won't show up on the input data object and therefore won't be available to downstream states.

To set an explicit key for the task state (recommended), pass a value for the key keyword argument. Otherwise, the key in the States dictionary will be generated automatically.

```python
data["foo_result"] = Foo(key="Do a foo")  # this will update the input data
Foo(key="Do a foo")  # this will not update the input data
```

### Passing data to tasks

By default, the input path to a task is the full data dict ($). If you want to pass part of the data to a task, provide a positional argument to the task constructor.

```python
data["foo_result"] = Foo(key="Do a foo")
data["bar_result"] = Bar(data["foo_result"], key="Do the bar")
```

### Stopping the execution

If you need to stop/cancel/abort the execution from within a task, you can use the  `context.stop_execution` method within your task's `run` method. A common use case is if you need to check the value of a feature flag at the beginning of the execution and abort if it's false. For example:

```python
if not some_condition:
    return await context.stop_execution()
```

You can provide extra detail by passing `error` and `cause` keyword arguments to the `stop_execution` method. The `error` is a short string like a code or enum value whereas `cause` is a longer description.

### Working with the State Data Client

One of the stated Step Functions best practices is to avoid passing large payloads between states; the input data limit is only 32K characters. To get around this, you can choose to store data from your task code in a DynamoDB table. With DynamoDB, we have an item limit of 400KB to work with. When you put items into the table you receive a pointer to the DynamoDB item which you can return from your task so it gets includes in the input data object. From there, since the pointer is in the `data` dict, you can reload the stored data in a downstream task. There is a library, `ns_sfn_tools`, with a State Data Client instance for putting and getting items from this DynamoDB table. It's available in your task's `run` method as `context.state_data_client`.

The client methods are split between "local" and "global" variants. Local methods operate on items stored within the project whereas global methods can operate on items that were stored from any project. Global methods require a fully-specified partition key (primary key, contains the execution ID) and table name to locate the item whereas local methods only need a simple key because the partition key and table name can be infered from the project automatically. The `put_*` methods return a dict with metadata about the location of the item, including the `key`, `partition_key`, and `table_name`. If you return this metadata object from a task, it will get put on the `data` object and you can call a `get_*` method later in the state machine.

Many methods also accept an optional `index` argument. This argument needs to be provided when getting/putting an item that was originally stored as part of a `put_items` or `put_global_items` call. Providing the `index` is usually only done within a map iteration task.

Below are a few of the more common methods:

#### `put_item`/`put_items`

The `put_item` method puts an item in the state store. It takes `key`, `data`, and `index` arguments. For example:

```python
context.state_data_client.put_item("characters", {"name": "jerry"})
context.state_data_client.put_item("characters", {"name": "elaine"}, index=24)
```

Note that the item at the given array index doesn't actually have to exist in the table before you call `put_item`. However, if it doesn't exist then you may have a fan-out logic bug upstream in your state machine.

The `put_items` method puts an entire list of items into the state store. Each item will be stored separately under its corresponding array index. For example:

```python
context.state_data_client.put_items("characters", [{"name": "jerry"}, {"name": "elaine"}])
```

#### `get_item`

The `get_item` method gets the data attribute from an item in the state store. It takes `key` and `index` arguments. For example:

```python
context.state_data_client.get_item("characters")  # -> {"name": "jerry"}
context.state_data_client.get_item("characters", index=24)  # -> {"name": "elaine"}
```

#### `get_item_for_map_iteration`/`get_global_item_for_map_iteration`

The `get_item_for_map_iteration` method gets the data attribute from an item in the state store using the `event` object. This method only works when called within a map iterator task. For example, if the `put_items` example above was called in a task, and its value was given to a map state to fan out, we can use the `get_item_for_map_iteration` method within our iterator task to fetch each item:

```python
# Iteration 0:
context.state_data_client.get_item_for_map_iteration(event)  # -> {"name": "jerry"}
# Iteration 1:
context.state_data_client.get_item_for_map_iteration(event)  # -> {"name": "elaine"}
```

This works because the map iterator state machine receives an input data object with the schema:

```json
{
  "items_result_table_name": "<DynamoDB table for the project>",
  "items_result_partition_key": "<execution ID>:characters",
  "items_result_key": "characters",
  "context_index": "<array index>",
  "context_value.$": "1"
}
```

The `get_item_for_map_iteration` is a helper method that uses that input to locate the right item. The `get_global_item_for_map_iteration` method has the same signature. It should be called when you know that the array used to fan out could have come from another project (e.g. the map state is the first state in a state machine triggered by a subscription).

### Error Handling

To handle an error in the task state, wrap it in a try/except statement. This will translate to an array of Catch objects within the rendered Task state.

```python
try:
    Foo()
except (KeyError, States.Timeout):
    TaskWhenFooHasErrored()
except:
    GenericTask()
```

```python
{
    "Type": "Task",
    "Resource": "...",
    "Catch": [
        {
            "Next": "foo_fail",
            "ErrorEquals": ["KeyError", "States.Timeout"],
        },
        {"Next": "foo_general", "ErrorEquals": ["States.ALL"]},
    ]
}
```

### Retries

To retry a task when it fails, use the retry context manager:

```python
with retry():
    MyTask()
```

You can configure the retry behavior by passing keyword arguments:

- `on_exceptions`: A list of Exception classes that will trigger another attempt (all exceptions by default)
- `interval`: An integer that represents the number of seconds before the first retry attempt (1 by default)
- `max_attempts`: A positive integer that represents the maximum number of retry attempts (3 by default)
- `backoff_rate`: The multiplier by which the retry interval increases during each attempt (2.0 by default)

For example:

```python
with retry(
    on_exceptions=[CustomError],
    interval=10,
    max_attempts=5,
    backoff_rate=1.0
):
    MyTask()
```

The retry context manager can only wrap a single task. If you want to also include error handling, the try statement should have the retry context manager as the one and only item in its body. For example:

```python
try:
    with retry():
        Foo()
except:
    GenericTask()
```

### [Choice](https://docs.aws.amazon.com/step-functions/latest/dg/amazon-states-language-choice-state.html)

To conditionally choose which logical path to traverse next in the state machine you can use Python boolean expressions.

Since the ASL form of the Choice state requires type-specific keys like StringEquals and NumericLessThan, but Python is an untyped language, we need a way to figure out the data types of the operands within conditional statements. One approach is to explicitly cast references to the data variable with the built-in function str, int, float, or bool. This enables Fluxio to generate type-appropriate configuration. If a reference to data isn't wrapped, Fluxio will assume it's a string for the boolean expression.

However, most of the time you don't need to explicitly wrap data values; Fluxio will automatically infer types from static, scalar values. This means that if you're comparing a value from data and a scalar value, Fluxio will use the scalar value type to pick the right ASL configuration. For example, for the comparison `data["foo"] > 0`, we know that 0 is a number and will pick the NumericGreaterThan operation.

Within the body of the conditional, you can include state code just like the main function. This will be translated to the Next key of the Choice branch.

The body of the else clause is translated to the Default key in the configuration.

```python
if data["foo"] > 0 and data["foo"] < 100:
    raise Bad("nope")
elif not bool(data["empty"]):
    return
elif data["empty"]["inner"] == "something":
    return
elif data["empty"]["inner"] == 4.25:
    parallel(branch1, branch2)
    if data["done"] != 10:
        raise DoneButNot()
elif data["array"][5] == 5:
    Bar()
    Baz()
else:
    raise Wrong("mmk")
```

```python
{
    "Type": "Choice",
    "Choices": [
        {
            "Next": "Fail-...",
            "And": [
                {"Variable": "$['foo']", "NumericGreaterThan": 0},
                {"Variable": "$['foo']", "NumericLessThan": 100},
            ],
        },
        {
            "Next": "Success-...",
            "Not": {
                "Variable": "$['empty']",
                "BooleanEquals": True,
            },
        },
        {
            "Next": "Success-...",
            "Variable": "$['empty']['inner']",
            "StringEquals": "something",
        },
        {
            "Next": "Parallel-...",
            "Variable": "$['empty']['inner']",
            "NumericEquals": 4.25,
        },
        {
            "Next": "bar2",
            "Variable": "$['array'][5]",
            "NumericEquals": 5,
        },
    ],
    "Default": "Fail-..."
}
```

**Note:** Timestamp comparison operators are not currently supported.

### [Map](https://docs.aws.amazon.com/step-functions/latest/dg/amazon-states-language-map-state.html)

To execute a dynamic number of nested state machines in parallel, you can use the Map state. First you need to define a module-level function that contains state machine logic in the body of the function just as you would in `main`. The function names are arbitrary as long as they're unique.

Then, within the main function, call the map function, passing a reference to an array in data and the iterator function as positional arguments:

```python
def item_iterator(data):
    Baz()

def main(data):
    map(data["items"], item_iterator)
```

If you want to limit the number of concurrently running items, provide a max_concurrency keyword arg:

```python
map(data["items"], item_iterator, max_concurrency=3)
```

### [Parallel](https://docs.aws.amazon.com/step-functions/latest/dg/amazon-states-language-parallel-state.html)

To execute multiple branches in parallel, you first need to define the branch states. Add a module-level function and include state machine logic in the body of the function just as you would in a main function. The function names are arbitrary as long as they're unique.

Then, within the main function, call the `parallel` function and pass it the branch function references as positional arguments:

```python
def branch1():
    Baz()

def branch2():
    Foo()

def main(data):
    parallel(branch1, Task2)
```

Note that the number of branches must be defined statically. If you need dynamic fan-out, use the Map state.

### [Pass](https://docs.aws.amazon.com/step-functions/latest/dg/amazon-states-language-pass-state.html)

Use this state to set static keys on the data variable. You can use subscript notation or the update method:

```python
# Set the key "debug" on the input data dict to be a static dictionary
data["debug"] = {"level": "INFO"}
# Set the key "more" on the input data dict to equal a static value
data.update({"more": 123})

# Not currently supported:
data["debug"].update({"level": "INFO"})
```

```python
{
    "Type": "Pass",
    "Result": {"level": "INFO"},
    "ResultPath": "$['debug']"
}
{
    "Type": "Pass",
    "Result": {"more": 123},
    "ResultPath": "$"
}
```

### [Succeed](https://docs.aws.amazon.com/step-functions/latest/dg/amazon-states-language-succeed-state.html)

To end the state machine execution and indicate a successful completion, include the return keyword within the main function.

### [Fail](https://docs.aws.amazon.com/step-functions/latest/dg/amazon-states-language-fail-state.html)

To end the state machine execution and indicate a failure, raise an exception. The exception class name will be used as the Error key and the optional string you pass to the exception constructor will b used as the Cause key.

```python
raise Wrong("mmk")
```

```python
{
    "Type": "Fail",
    "Error": "Wrong",
    "Cause": "mmk"
}
```

### [Wait](https://docs.aws.amazon.com/step-functions/latest/dg/amazon-states-language-wait-state.html)

If you want to pause the execution of the state machine, you can call a function called wait with either a seconds or timestamp keyword argument. The value of the argument can be a static value or input data reference:

```python
# Wait 10 seconds
wait(seconds=10)
wait(seconds=data["wait_in_seconds"])

# Wait until a future time
wait(timestamp="2020-08-18T17:33:00Z")
wait(timestamp=data["timestamp"])
```

## Decorators

Fluxio supports additional configuration of the state machine via Python decorators. These are meant to configure pre- and post-execution hooks (i.e. something "outside" the execution), like a schedule trigger or notification topic.

### schedule

To trigger an execution on a recurring schedule, wrap the main function in a schedule decorator:

```python
@schedule(expression="rate(1 hour)")
def main(data):
    MyTask()
```

The expression keyword argument can either be a cron or rate expression. See the [documentation for ScheduledEvents](https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/ScheduledEvents.html) for more details on the expression format.

### subscribe

To trigger an execution when a message is published to an SNS topic from another project, wrap the function in a subscribe decorator:

```python
@subscribe(project="other-project")
def main(data):
    MyTask()
```

By default, this will subscribe to successful execution events published for the main state machine in the project named other-project. The project keyword argument refers to the folder name of another project.

Other keyword arguments:

- `state_machine`: The identifier of a state machine function in the source project. By default this is "main", but this allows subscriptions to other exported state machines.
- `status`: One of "success" (default) or "failure". This represents the execution status of the source state machine execution. It will be used to select which of the two SNS topics from the source project to subscribe to.

Fluxio will take the project and state_machine arguments and pick the right ImportValue based on the CloudFormation stack and environment.

If you want to subscribe to an explicit SNS topic that has been exported from another stack outside of Fluxio, you can provide the `topic_arn_import_value` keyword argument instead:

```python
@subscribe(topic_arn_import_value="${Environment}-my-topic-arn")
def main(data):
    MyTask()
```

The value for this argument can be a simple string but can also include any CloudFormation substitution variables that you have access to in the template since the string will be wrapped in [`!Sub`](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference-sub.html). These include parameters and resources references.

### export

To explicitly "export" a state machine, wrap the function in an export decorator:

```python
@export()
def some_state_machine(data):
    MyTask()
```

An "exported" state machine gets its own CloudFormation template and can be directly executed.

You only need to use the export decorator if:

- You have multiple state machines in a project.py file
- AND one of them is nested in another
- AND you want to be able to directly execute the nested state machine
- AND the nested state machine function isn't already wrapped in schedule or subscribe (those decorators cause the state machine to be exported automatically)
