from datetime import datetime
from enum import Enum

from flask_restx import fields

from esg_lib.convertible import _is_convertible

DEFAULT_MAPPING = {
    "bool": "nullable boolean",
    "str": "nullable string",
    "int": "nullable integer",
    "float": "nullable float",
    "datetime": "nullable datetime",
    "Enum": "nullable enum"
}


def get_restx_field(field_type, is_required, default_value):
    meta_data = {
        "required": is_required,
    }

    if DEFAULT_MAPPING.get(field_type.__name__) or issubclass(field_type, Enum):
        if issubclass(field_type, Enum) and default_value:
            default_value = default_value.value
        if default_value is None and not is_required:
            default_value = DEFAULT_MAPPING.get(field_type.__name__)
        if default_value:
            meta_data["default"] = default_value

    if field_type == bool:
        return fields.Boolean(**meta_data)
    elif field_type == str:
        return fields.String(**meta_data)
    elif field_type == int:
        return fields.String(**meta_data)
    elif field_type == float:
        return fields.Float(**meta_data)
    elif field_type == datetime:
        return fields.DateTime(**meta_data)
    elif issubclass(field_type, Enum):
        return fields.String(**meta_data)
    else:
        return fields.Raw(**meta_data)


def convertibleclass_to_namespace_model(cls, namespace, model_name: str):
    result = {}

    for field_name, field in cls.__dataclass_fields__.items():
        field_type = field.type
        if _is_convertible(field_type): # if the field type is a convertible class then create a nested field
            result[field_name] = fields.Nested(convertibleclass_to_namespace_model(field_type, namespace, field_type.__name__))
        else:
            is_required = cls.__dataclass_fields__.get(field_name).metadata.get("required", False)
            default_value = field.default

            if isinstance(field_type, list):
                if _is_convertible(field_type[0]):
                    result[field_name] = fields.List(fields.Nested(convertibleclass_to_namespace_model(field_type[0], namespace, field_type[0].__name__)), required=is_required)
                else:
                    result[field_name] = fields.List(get_restx_field(field_type[0], is_required, default_value), required=is_required)
            else:
                result[field_name] = get_restx_field(field_type, is_required, default_value)

    return namespace.model(
        model_name,
        result
    )
