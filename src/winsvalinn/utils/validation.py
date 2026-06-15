"""
Input Validation Module

Provides validation functions for user inputs to prevent crashes
and provide helpful error messages.
"""

from winsvalinn.utils.logger import ModuleLogger

logger = ModuleLogger("InputValidation")


class ValidationError(Exception):
    """Custom exception for validation errors."""

    pass


def validate_port_range(start, end):
    """
    Validate port range input.

    Args:
        start: Start port (can be string or int)
        end: End port (can be string or int)

    Returns:
        tuple: (start_port, end_port) as integers

    Raises:
        ValidationError: If validation fails with helpful message
    """
    try:
        start_port = int(start)
        end_port = int(end)
    except (ValueError, TypeError):
        logger.error(f"Port range not numeric: start={start}, end={end}")
        raise ValidationError(
            "Port numbers must be integers.\n\n"
            f"You entered: start='{start}', end='{end}'\n"
            "Please enter numbers between 1 and 65535."
        )

    if not (1 <= start_port <= 65535):
        logger.error(f"Invalid start port: {start_port}")
        raise ValidationError(
            f"Start port must be between 1 and 65535.\n\n"
            f"You entered: {start_port}\n"
            "Valid ports: 1-65535"
        )

    if not (1 <= end_port <= 65535):
        logger.error(f"Invalid end port: {end_port}")
        raise ValidationError(
            f"End port must be between 1 and 65535.\n\n"
            f"You entered: {end_port}\n"
            "Valid ports: 1-65535"
        )

    if start_port > end_port:
        logger.error(f"Invalid range: {start_port} > {end_port}")
        raise ValidationError(
            f"Start port must be less than or equal to end port.\n\n"
            f"You entered: {start_port} - {end_port}\n"
            "Please swap the values or correct them."
        )

    range_size = end_port - start_port + 1
    if range_size > 10000:
        logger.warning(f"Large port range requested: {range_size} ports")
        raise ValidationError(
            f"Port range too large: {range_size} ports.\n\n"
            f"You entered: {start_port} - {end_port}\n"
            "Maximum recommended range: 10000 ports\n\n"
            "Large ranges can take a long time to scan.\n"
            "Consider scanning in smaller chunks."
        )

    logger.info(f"Port range validated: {start_port}-{end_port} ({range_size} ports)")
    return start_port, end_port


def validate_file_path(path, must_exist=False, must_be_file=True):
    """
    Validate file path.

    Args:
        path: File path to validate
        must_exist: If True, file must exist
        must_be_file: If True, path must be a file (not directory)

    Returns:
        str: Validated absolute path

    Raises:
        ValidationError: If validation fails
    """
    import os

    if not path or not isinstance(path, str):
        raise ValidationError("File path cannot be empty.\n\nPlease select a valid file.")

    abs_path = os.path.abspath(path)

    if must_exist:
        if not os.path.exists(abs_path):
            logger.error(f"File not found: {abs_path}")
            raise ValidationError(
                f"File not found:\n\n{abs_path}\n\nPlease check the path and try again."
            )

        if must_be_file and not os.path.isfile(abs_path):
            logger.error(f"Path is not a file: {abs_path}")
            raise ValidationError(
                f"Path is not a file:\n\n{abs_path}\n\nPlease select a file, not a directory."
            )

    logger.info(f"File path validated: {abs_path}")
    return abs_path


def validate_positive_integer(value, name="Value", min_val=1, max_val=None):
    """
    Validate positive integer input.

    Args:
        value: Value to validate
        name: Name of the field (for error messages)
        min_val: Minimum allowed value
        max_val: Maximum allowed value (None for no max)

    Returns:
        int: Validated integer

    Raises:
        ValidationError: If validation fails
    """
    try:
        int_value = int(value)
    except (ValueError, TypeError):
        raise ValidationError(
            f"{name} must be a number.\n\n"
            f"You entered: '{value}'\n"
            f"Please enter a number >= {min_val}"
        )

    if int_value < min_val:
        raise ValidationError(f"{name} must be at least {min_val}.\n\nYou entered: {int_value}")

    if max_val is not None and int_value > max_val:
        raise ValidationError(f"{name} must be at most {max_val}.\n\nYou entered: {int_value}")

    return int_value


def validate_choice(value, choices, name="Option"):
    """
    Validate value is in allowed choices.

    Args:
        value: Value to validate
        choices: List/set of allowed values
        name: Name of the field

    Returns:
        Original value if valid

    Raises:
        ValidationError: If not in choices
    """
    if value not in choices:
        choices_str = ", ".join(str(c) for c in choices)
        raise ValidationError(
            f"Invalid {name}.\n\nYou selected: {value}\nValid options: {choices_str}"
        )

    return value
