from flask_restx import Namespace, fields


class NullableString(fields.String):
    __schema_type__ = ["string", "null"]
    __schema_example__ = "nullable string"


class NullableInteger(fields.Integer):
    __schema_type__ = ["integer", "null"]
    __schema_example__ = "nullable integer"


class NullableFloat(fields.Float):
    __schema_type__ = ["number", "null"]
    __schema_example__ = "nullable float"


class AuditDto:
    api = Namespace("Audit")

    user_info = api.model(
        "User",
        {
            "fullname": fields.String(required=True),
            "email": fields.String(required=True),
        },
    )

    audit_info = api.model(
        "Audit Info",
        {
            "id": fields.String(required=True),
            "collection": NullableString(),
            "action": fields.String(required=True),
            "user": fields.Nested(user_info),
            "old_value": fields.Raw(),
            "new_value": fields.Raw(),
            "created_on": fields.DateTime(),
        },
    )

    audit_pagination = api.model(
        "Audit page",
        {
            "page": fields.Integer,
            "size": fields.Integer,
            "total": fields.Integer,
            "content": fields.List(fields.Nested(audit_info), skip_none=True),
        },
    )
