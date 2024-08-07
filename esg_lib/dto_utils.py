from datetime import datetime
from enum import Enum

from flask_restx import fields

from esg_lib.convertible import _is_convertible
from esg_lib.dto import NullableString, NullableInteger, NullableFloat, NullableBoolean


def convertibleclass_to_namespace_model(cls, namespace, model_name: str):
    result = {}

    for field_name, field in cls.__dataclass_fields__.items():
        field_type = field.type
        if _is_convertible(field_type):
            result[field_name] = fields.Nested(convertibleclass_to_namespace_model(field_type, namespace, field_type.__name__))
        else:
            is_required = cls.__dataclass_fields__.get(field_name).metadata.get("required", False)
            if field_type == bool:
                if is_required:
                    result[field_name] = fields.Boolean(required=True)
                else:
                    result[field_name] = NullableBoolean()
            elif field_type == str:
                if is_required:
                    result[field_name] = fields.String(required=True)
                else:
                    result[field_name] = NullableString()
            elif field_type == int:
                if is_required:
                    result[field_name] = fields.Integer(required=True)
                else:
                    result[field_name] = NullableInteger()
            elif field_type == float:
                if is_required:
                    result[field_name] = fields.Float(required=True)
                else:
                    result[field_name] = NullableFloat()
            elif field_type == datetime:
                result[field_name] = fields.DateTime()
            elif isinstance(field_type, list):
                if _is_convertible(field_type[0]):
                    result[field_name] = fields.List(fields.Nested(convertibleclass_to_namespace_model(field_type[0], namespace, field_type[0].__name__)))
                elif field_type[0] == str:
                    if is_required:
                        result[field_name] = fields.List(fields.String())
                    else:
                        result[field_name] = fields.List(NullableString())
                elif field_type[0] == int:
                    if is_required:
                        result[field_name] = fields.List(fields.Integer())
                    else:
                        result[field_name] = fields.List(NullableInteger())
                elif field_type[0] == float:
                    if is_required:
                        result[field_name] = fields.List(fields.Float())
                    else:
                        result[field_name] = fields.List(NullableFloat())
                elif field_type[0] == datetime:
                    result[field_name] = fields.List(fields.DateTime())
            elif issubclass(field_type, Enum):
                result[field_name] = fields.String()
            else:
                result[field_name] = fields.Raw()

    # return result
    return namespace.model(
        model_name,
        result
    )
    # if not (ignore_date_time and isinstance(val, datetime)) and field_to_value and val is not None:
    #     val = field_to_value(val)

    # if isinstance(val, (list, tuple)):
    #     pass
