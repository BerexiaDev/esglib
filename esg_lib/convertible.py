import logging
import os
import re
from collections import defaultdict
from dataclasses import dataclass, fields, field, MISSING, Field
from datetime import datetime
from decimal import Decimal
from enum import EnumMeta, Enum
from typing import Union, Optional, Any, Iterable

import aenum
from flask import g

from esg_lib.convertible_utils import validate_range

logger = logging.getLogger(__name__)
__FIELDS = "_____CONVERTIBLE______"


def _is_convertible(_cls):
    if hasattr(_cls, __FIELDS):
        return True

    return False


def _extract_metadata_callable(f, callable_name):
    if hasattr(f, "metadata"):
        if callable_name in f.metadata and hasattr(
            f.metadata[callable_name], "__call__"
        ):
            return f.metadata[callable_name]

    return None


def _extract_metadata_boolean(f, boolean_name):
    if hasattr(f, "metadata"):
        if boolean_name in f.metadata and isinstance(f.metadata[boolean_name], bool):
            return f.metadata[boolean_name]

    return False


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


def default_field(*args, **kwargs):
    kwargs.update({"default": None})
    return field(*args, **kwargs)


def required_field(*args, **kwargs):
    metadata = kwargs.pop("metadata", {})
    default = kwargs.pop("default", None)
    required_metadata = meta(required=True)
    metadata.update(required_metadata)
    kwargs.update(
        {
            "default": default,
            "metadata": metadata,
        }
    )
    return field(*args, **kwargs)


def url_field(*args, **kwargs):
    metadata = kwargs.pop("metadata", {})
    default = kwargs.pop("default", None)
    url_metadata = meta(value_to_field=strip_url, field_to_value=strip_url)
    metadata.update(url_metadata)
    kwargs.update({"default": default, "metadata": metadata})
    return field(*args, **kwargs)


def positive_integer_field(*args, **kwargs):
    metadata = kwargs.pop("metadata", {})
    validator_metadata = meta(
        validator=validate_range(min_=0),
        value_to_field=int,
        required=metadata.get("required", False),
    )
    metadata.update(validator_metadata)
    kwargs.update({"metadata": metadata})
    return field(*args, **kwargs)


def natural_number_field(*args, **kwargs):
    metadata = kwargs.pop("metadata", {})
    validator_metadata = meta(validator=validate_range(min_=1), value_to_field=int)
    metadata.update(validator_metadata)
    kwargs.update({"metadata": metadata})
    return field(*args, **kwargs)


def dict_field(nested_cls, *args, **kwargs):
    def from_converter(body: dict) -> dict:
        if not body or not hasattr(nested_cls, "from_dict"):
            return body
        return {key: nested_cls.from_dict(value) for key, value in body.items()}

    def to_converter(body: dict) -> dict:
        if not body or not hasattr(nested_cls, "to_dict"):
            return body
        return {key: val.to_dict(include_none=False) for key, val in body.items()}

    metadata = kwargs.pop("metadata", {})
    dict_metadata = meta(value_to_field=from_converter, field_to_value=to_converter)
    metadata.update(dict_metadata)
    kwargs.update({"metadata": metadata})
    return field(*args, **kwargs)


def strip_url(url: str) -> str:
    return url.strip() if url else url


def get_field(cls, field_name: str):
    """Finds the dataclass field by name"""
    return next(filter(lambda x: x.name == field_name, fields(cls)), None)


def _get_field_type(f) -> Optional[type]:
    if not hasattr(f, "type"):
        return

    field_type = f.type
    if isinstance(f.type, str):
        # Check if string is a Platform Play class name and convert to class type if so
        field_type = globals().get("registered_class", {}).get(f.type)
        if not field_type:
            raise RuntimeError(
                "Please don't import annotations from __future__. read more here [https://bugs.python.org/issue34776]"
            )
    return field_type


def set_field_value(
    self,
    field: Union[str, Field],
    field_value: Any,
    use_validator_field=True,
    field_ignored_list = None,
):
    """
    Sets value to a class field after passing all validation and conversion.
    NOTE: this method is intended to be a class method!
    """
    cls = type(self)
    f = field
    if not isinstance(field, Field):
        f = get_field(self, field)
        if not f:
            raise Exception(
                "No field [{}] in class [{}]".format(cls.__name__, field)
            )

    field_required = _extract_metadata_boolean(f, REQUIRED)
    if field_value is MISSING:
        if field_required and use_validator_field:
            raise Exception(
                "Field [{}.{}] is mandatory".format(cls.__name__, f.name)
            )
        return

    return _serialize_and_set_field_value(
        self, f, field_value, use_validator_field, field_ignored_list
    )


def _serialize_and_set_field_value(
    self,
    f: Field,
    field_value: Any,
    use_validator_field=True,
    field_ignored_list = None,
):
    cls = type(self)
    field_validator = _extract_metadata_callable(f, VALIDATOR)
    field_required = _extract_metadata_boolean(f, REQUIRED)
    value_to_field = _extract_metadata_callable(f, VAL_TO_FIELD)

    field_type = _get_field_type(f)

    try:
        if value_to_field:
            field_value = value_to_field(field_value)

        if field_validator is not None and use_validator_field:
            try:
                validated_ok = field_validator(field_value)
            except Exception as e:
                raise Exception(
                    "Validation function error for [{}.{}] field with error [{}]".format(
                        cls.__name__, f.name, e.args
                    )
                )

            if type(field_validator) is not type and not validated_ok:
                # If the validator is a simple type e.g. bool, int, field_validator will return the value, and
                # we must allow False/0/empty string.
                logger.warning("Field error [{}.{}]".format(cls.__name__, f.name))
                raise Exception(
                    "Field error [{}.{}]".format(cls.__name__, f.name)
                )

        is_list_type = isinstance(field_type, list) or is_from_generic_list(field_type)
        if is_list_type and not isinstance(field_value, list):
            raise Exception(
                f"[{field_value}] Field type is list but field value {f.name} is not"
            )

        if is_list_field(field_type, field_value):
            _handle_list_values(
                cls,
                f.name,
                field_type,
                field_validator,
                field_value,
                self,
                use_validator_field,
                field_ignored_list,
            )
        elif not isinstance(field_type, list):
            val = _from_single_value(
                field_type,
                field_validator,
                field_value,
                use_validator_field,
                field_required,
                field_ignored_list,
            )
            setattr(self, f.name, val)
    except CreateSingleValueWrongTypeError:
        raise Exception(
            "Field [{}.{}] with value [{}] is not type of [{}]".format(
                cls.__name__, f.name, field_value, field_type.__name__
            )
        )
    except Exception as e:
        raise e
    except Exception as e:
        raise Exception(
            "Field [{}.{}] with value [{}] has error [{}]".format(
                cls.__name__, f.name, field_value, e.args
            )
        )


def convert_ignored_fields_to_dict(ignored_fields: Iterable):
    ignored_fields_mapping = defaultdict(list)
    if ignored_fields is None:
        return ignored_fields_mapping

    nested_ignore_fields = [f for f in ignored_fields if "." in f]
    for f in nested_ignore_fields:
        ignore_key = f.split(".")[0]
        ignore_value = f.split(f"{ignore_key}.", maxsplit=1)[1]
        ignored_fields_mapping[ignore_key].append(ignore_value)

    return ignored_fields_mapping


def from_dict(
    cls, d: dict, use_validator_field=True, ignored_fields: Union[list, tuple] = None
):
    new_instance = cls()
    # Generating {field: [field_nested_ignore_value_1, field_nested_ignore_value_2]} dictionary to ignore nested fields
    nested_ignore_dict = convert_ignored_fields_to_dict(ignored_fields)

    for f in fields(cls):
        field_name = f.name
        if field_name == "id":
            setattr(new_instance, field_name, d.get("id") or d.get("_id"))
            continue

        if field_name.startswith("_"):
            continue

        if field_name[0].isupper():
            continue

        if isinstance(ignored_fields, (list, tuple)) and field_name in ignored_fields:
            setattr(new_instance, field_name, d[field_name])
            continue

        field_ignored_list = nested_ignore_dict.get(f.name)
        set_field_value(
            new_instance,
            f,
            d[f.name] if f.name in d else MISSING,
            use_validator_field,
            field_ignored_list,
        )

    if hasattr(cls, "validate") and use_validator_field:
        cls.validate(new_instance)
    if hasattr(cls, "post_init"):
        new_instance.post_init()
    return new_instance


class CreateSingleValueWrongTypeError(ValueError):
    """It wasn't possible to deserialize single element"""


def _get_enum_value(field_type: aenum.Enum, field_value):
    try:
        if isinstance(field_value, bool):
            raise ValueError

        return field_type(field_value)
    except ValueError:
        return field_type[field_value]


def _from_single_value(
    field_type,
    field_validator,
    field_value,
    use_validator_field,
    field_required,
    ignored_fields=None,
):
    if field_value is None and not field_required:
        return field_value

    elif isinstance(field_value, int) and field_validator is float:
        # WARN: The opposite is not tolerable and MUST NOT be implemented
        return float(field_value)

    elif (
        isinstance(field_value, float)
        and isinstance(field_type, float)
        and _is_convertible(field_type)
    ):
        return Decimal(str(field_value))

    elif isinstance(field_value, Decimal):
        if field_validator is float:
            return float(field_value)

        elif field_validator is int:
            return int(field_value)

    elif isinstance(field_value, dict) and _is_convertible(field_type):
        return field_type.from_dict(
            field_value,
            use_validator_field=use_validator_field,
            ignored_fields=ignored_fields,
        )

    elif isinstance(field_type, EnumMeta):
        try:
            return _get_enum_value(field_type, field_value)

        except KeyError as e:
            raise CreateSingleValueWrongTypeError from e

    elif field_type == Any:
        return field_value

    else:
        if field_type is not None and not isinstance(field_value, field_type):
            raise CreateSingleValueWrongTypeError(
                f"{field_value} is not of type {field_type}"
            )

        return field_value


def _handle_list_values(
    cls,
    field_name,
    field_type,
    field_validator,
    field_value,
    new_instance,
    use_validator_field,
    field_ignored_list=None,
):
    field_instance_type = _calculate_list_field_instance_type(field_type)
    if isinstance(field_instance_type, str):
        # If str, check if it's a known registered Platform Play class
        # and convert field_instance_type from str to class type
        pp_class = globals().get("registered_class", {}).get(field_instance_type)
        if pp_class:
            field_instance_type = pp_class
    if _is_convertible(field_instance_type):
        elements = [
            item
            if isinstance(item, field_instance_type)
            else field_instance_type.from_dict(item, use_validator_field)
            for item in field_value
        ]
        setattr(new_instance, field_name, elements)
    else:
        try:
            elements = [
                _from_single_value(
                    field_instance_type,
                    field_validator,
                    item,
                    use_validator_field,
                    True,
                    field_ignored_list,
                )
                for item in field_value
            ]
            setattr(new_instance, field_name, elements)
        except CreateSingleValueWrongTypeError as e:
            raise ValueError(
                "List Field [{}.{}] with value [{}] is not type of [{}]".format(
                    cls.__name__, field_name, field_value, field_instance_type.__name__
                )
            ) from e

        except Exception:
            raise Exception(
                "List Field [{}.{}] with value [{}] is not type of [{}]".format(
                    cls.__name__, field_name, field_value, field_instance_type.__name__
                )
            )


def _calculate_list_field_instance_type(field_type):
    if is_from_generic_list(field_type):
        field_instance_type = field_type.__args__[0]
    else:
        field_instance_type = field_type[0]
    return field_instance_type


def is_from_generic_list(field_type):
    try:
        return field_type.__origin__ == list

    except Exception:
        return False


def is_list_field(field_type, field_value):
    value_is_list = isinstance(field_value, list)
    field_type_is_list = isinstance(field_type, list) or field_type == list
    return (value_is_list and field_type_is_list) or is_from_generic_list(field_type)


def reset_attributes(self, attributes=None, raise_error=False):
    for attribute in attributes:
        cls_field = get_field(self, attribute)
        if cls_field is None:
            if raise_error:
                raise AttributeError(attribute)
            continue

        setattr(self, attribute, cls_field.default)


def to_dict(
    self,
    include_none=True,
    ignored_fields: Union[list, tuple] = None,
    exclude_fields: Union[list, tuple] = None,
    ignore_date_time: bool = False,
):
    if not hasattr(self, "__dict__"):
        return self

    result = {}
    # Generating {field: [field_nested_ignore_value_1, field_nested_ignore_value_2]} dictionary to ignore nested fields
    nested_ignore_dict = convert_ignored_fields_to_dict(ignored_fields)

    for key, val in self.__dict__.items():

        if exclude_fields and key in exclude_fields:
            continue

        key_ignore_fields = nested_ignore_dict.get(key)
        if key.startswith("_") or key[0].isupper():
            continue

        if isinstance(ignored_fields, (list, tuple)) and key in ignored_fields:
            result[key] = val
            continue

        field = self.__dataclass_fields__.get(key)
        field_to_value = _extract_metadata_callable(field, FIELD_TO_VAL)

        if not (ignore_date_time and isinstance(val, datetime)) and field_to_value and val is not None:
            val = field_to_value(val)

        if isinstance(val, (list, tuple)):
            element = [
                _to_single_value(item, include_none, key_ignore_fields, ignore_date_time) for item in val
            ]
        else:
            element = _to_single_value(val, include_none, key_ignore_fields, ignore_date_time)

        if include_none:
            result[key] = element
        elif element is not None and val is not None:
            result[key] = element
    return result


def _to_single_value(
    val, include_none: bool, ignored_fields: Union[list, tuple] = None, ignore_date_time: bool = False
):
    if isinstance(val, aenum.StrEnum):
        return val.value

    if isinstance(val, Enum):
        first_enum = [item for item in val.__class__][0]
        if isinstance(first_enum, int):
            return int(val)

        return val.name

    elif isinstance(val, Decimal):
        return float(val)

    elif isinstance(val, (dict, datetime)):
        return val
    else:
        return to_dict(val, include_none, ignored_fields, ignore_date_time=ignore_date_time)


def find_match_and_replace(value, to_type: type = None):
    pattern = re.compile(r".*?\${(\w+)}.*?")
    match = pattern.findall(value)  # to find all env variables in line
    for g in match or []:
        new_value = value.replace(f"${{{g}}}", os.environ.get(g, g))
        if to_type == int:
            return int(new_value)
        elif to_type == bool:
            if new_value == "true":
                return True
            elif new_value == "false":
                return False
        return new_value


registered_class = {}


def init_method(self, *args, **kwargs):
    g.table_name = self.__TABLE__


def convertibleclass(_cls):
    """Keep track of a class"""
    registered_class[_cls.__name__] = _cls
    _cls = dataclass(_cls)
    setattr(_cls, __FIELDS, _cls.__name__)
    _cls.to_dict = to_dict
    _cls.__init__ = init_method
    _cls.from_dict = classmethod(from_dict)
    _cls.reset_attributes = reset_attributes
    _cls.set_field_value = set_field_value
    return _cls
