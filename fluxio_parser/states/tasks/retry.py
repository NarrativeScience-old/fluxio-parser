"""Contains class to add retry logic to tasks"""
import ast
from typing import Dict, List

from fluxio_parser.util import CallableOption, GET_VALUE_MAP, serialize_error_name

RETRY_OPTION_MAP = {
    "on_exceptions": CallableOption(
        value_type=ast.List,
        value_type_label="list",
        get_value=lambda node, visitor: [
            serialize_error_name(elt) for elt in node.elts
        ],
        default_value=["Exception"],
    ),
    "interval": CallableOption(
        value_type=ast.Num,
        value_type_label="integer",
        get_value=GET_VALUE_MAP[int],
        default_value=1,
    ),
    "max_attempts": CallableOption(
        value_type=ast.Num,
        value_type_label="integer",
        get_value=GET_VALUE_MAP[int],
        default_value=3,
    ),
    "backoff_rate": CallableOption(
        value_type=ast.Num,
        value_type_label="float",
        get_value=GET_VALUE_MAP[float],
        default_value=2.0,
    ),
}


class Retry:
    """Class for holding retry configuration"""

    def __init__(
        self,
        on_exceptions: List[str] = ["Exception"],
        interval: int = 1,
        max_attempts: int = 3,
        backoff_rate: float = 2.0,
    ) -> None:
        """Initialize a Retry

        Args:
            on_exceptions: names of exceptions that will trigger a retry attempt
            interval: the number of seconds before the first retry attempt
            max_attempts: the maximum number of retry attempts
            backoff_rate: multiplier by which the retry interval increases after
                each attempt

        """
        self.on_exceptions = on_exceptions
        self.interval = interval
        self.max_attempts = max_attempts
        self.backoff_rate = backoff_rate

    def to_dict(self) -> Dict:
        """Convert this Retry to a dictionary

        Returns:
            Serialized version of the Retry configuration

        """
        return {
            "ErrorEquals": self.on_exceptions,
            "IntervalSeconds": self.interval,
            "MaxAttempts": self.max_attempts,
            "BackoffRate": self.backoff_rate,
        }
