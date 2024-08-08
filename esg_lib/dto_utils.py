from datetime import datetime
from enum import Enum

from flask_restx import fields

from esg_lib.convertible import _is_convertible


def get_restx_field(field_type, is_required, default_value):
    if field_type == bool:
        if is_required:
            return fields.Boolean(required=True)
        else:
            default_value = default_value or "nullable boolean"
            return fields.Boolean(default=default_value)
    elif field_type == str:
        if is_required:
            return fields.String(required=True)
        else:
            default_value = default_value or "nullable string"
            return fields.String(default=default_value)
    elif field_type == int:
        if is_required:
            return fields.Integer(required=True)
        else:
            default_value = default_value or "nullable integer"
            return fields.String(default=default_value)
    elif field_type == float:
        if is_required:
            return fields.Float(required=True)
        else:
            default_value = default_value or "nullable float"
            return fields.Float(default=default_value)
    elif field_type == datetime:
        if is_required:
            return fields.DateTime(required=True)
        else:
            default_value = default_value or datetime.now()
            return fields.DateTime()
    elif issubclass(field_type, Enum):
        if is_required:
            return fields.String(required=True)
        else:
            default_value = default_value.value if default_value else "nullable enum"
            return fields.String(default=default_value)
    else:
        return fields.Raw()


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
                    result[field_name] = fields.List(fields.Nested(convertibleclass_to_namespace_model(field_type[0], namespace, field_type[0].__name__)))
                else:
                    result[field_name] = fields.List(get_restx_field(field_type[0], is_required, default_value))
            else:
                result[field_name] = get_restx_field(field_type, is_required, default_value)

    return namespace.model(
        model_name,
        result
    )
