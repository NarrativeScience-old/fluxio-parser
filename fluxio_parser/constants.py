"""Contains constants"""
import re

#: Set of input data keys that are used internally. These keys cannot be used in a
#: ResultPath.
RESERVED_INPUT_DATA_KEYS = {"__trace"}

#: A ResultPath is invalid if it matches this pattern
INVALID_RESULT_PATH_PATTERN = re.compile("|".join(RESERVED_INPUT_DATA_KEYS))
