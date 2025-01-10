from flask_restx import Resource
from flask import request

# from esg_lib.dto import CommonDto

from esg_lib.audit_logger.service.audit_service import get_audit_logs_paginated
from esg_lib.dto import AuditDto
from esg_lib.reqparse import get_default_paginated_request_parse

api = AuditDto.api
audit_pagination = AuditDto.audit_pagination


@api.route("/search")
class AuditSearch(Resource):
    @api.doc("Get Audit logs")
    # @api.expect(CommonDto.search_dto, validate=True)
    @api.marshal_list_with(audit_pagination, skip_none=True)
    @api.response(200, "Audit log successfully retrieved paginated.")
    def post(self):
        parser = get_default_paginated_request_parse()
        parser.remove_argument("search_value")
        args = parser.parse_args()
        return get_audit_logs_paginated(args, request.json)
