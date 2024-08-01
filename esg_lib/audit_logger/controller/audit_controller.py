from flask_restx import Resource, reqparse

from esg_lib.audit_logger.service.audit_service import get_audit_logs_paginated
from esg_lib.dto import AuditDto
from esg_lib.reqparse import get_default_paginated_request_parse

api = AuditDto.api
audit_pagination = AuditDto.audit_pagination


@api.route("")
class Audit(Resource):
    @api.doc("Get Audit logs")
    @api.marshal_list_with(audit_pagination, skip_none=True)
    @api.response(200, "Audit log successfully retrieved paginated.")
    def get(self):
        parser = get_default_paginated_request_parse()
        parser.remove_argument("search_value")
        parser.add_argument("table_names", location="args")
        parser.add_argument("actions", location="args")
        args = parser.parse_args()
        return get_audit_logs_paginated(args)
