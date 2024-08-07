import re
from datetime import datetime
from typing import Union, Mapping


ACRONYM_RE = re.compile(r"([A-Z]+)(?=[A-Z][a-z])")
SPLIT_RE = re.compile(r"([\-_\s]*[A-Z0-9]+[^A-Z\-_\s]+[\-_\s]*)")
UNDERSCORE_RE = re.compile(r"([^\-_\s])[\-_\s]+([^\-_\s])")


VALIDATOR = "validator"
REQUIRED = "required"
VAL_TO_FIELD = "val_to_field"
FIELD_TO_VAL = "field_to_val"


def meta(
    validator=None, required: bool = False, field_to_value=None, value_to_field=None
) -> dict:
    result = {}
    if validator is not None:
        result[VALIDATOR] = validator
    if required is not None:
        result[REQUIRED] = required
    if value_to_field:
        result[VAL_TO_FIELD] = value_to_field
    if field_to_value:
        result[FIELD_TO_VAL] = field_to_value
    return result


def validate_range(min_: Union[int, float] = None, max_: Union[int, float] = None):
    def validator(value):
        if min_ is not None and max_ is not None:
            msg = f"value must be between {min_} and {max_}"
            valid = min_ <= value <= max_
        elif min_ is not None:
            msg = f"value must be above or equal to {min_}"
            valid = min_ <= value
        elif max_ is not None:
            msg = f"value must be below or equal to {max_}"
            valid = value <= max_
        else:
            raise TypeError(
                "At least one of arguments should be provided: 'min_number', 'max_number'"
            )

        if not valid:
            raise Exception(msg)

        return True

    return validator


def _process_keys(str_or_iter, fn):
    if isinstance(str_or_iter, list):
        return [_process_keys(k, fn) for k in str_or_iter]
    elif isinstance(str_or_iter, Mapping):
        return {fn(k): _process_keys(v, fn) for k, v in str_or_iter.items()}
    else:
        return str_or_iter


def separate_words(string, separator="_", split=SPLIT_RE.split):
    return separator.join(s for s in split(string) if s)


def utc_str_field_to_val(val: Union[str, datetime]) -> str:
    if isinstance(val, str):
        return val

    try:
        return val.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    except AttributeError:
        raise Exception(f"{val} is invalid date format")


def utc_str_val_to_field(val: Union[str, datetime]) -> datetime:
    if isinstance(val, datetime):
        return val

    try:
        return datetime.strptime(val, "%Y-%m-%dT%H:%M:%S.%fZ")
    except TypeError:
        raise Exception(f"{val} is invalid date format")
    except ValueError:
        try:
            return datetime.strptime(val, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            raise Exception(f"{val} is invalid date format")


def default_datetime_meta():
    return meta(
        field_to_value=utc_str_field_to_val, value_to_field=utc_str_val_to_field
    )
