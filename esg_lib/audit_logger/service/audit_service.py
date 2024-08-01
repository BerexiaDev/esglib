from esg_lib.audit_logger.models.AuditLog import AuditLog
from esg_lib.decorators import catch_exceptions
from esg_lib.paginator import Paginator


@catch_exceptions
def get_audit_logs_paginated(args):
    query = {}

    table_names = args.get("table_names")
    actions = args.get("actions")
    page = args.get("page")
    per_page = args.get("size")
    sort_by = args.get("sort_key", "id")
    sort_order = args.get("sort_order", -1)

    if "RETRIEVE" not in actions:
        query.update({"action": {"$ne": "RETRIEVE"}})

    if actions:
        query.update({"action": {"$in": actions.split(',')}})

    if table_names:
        query.update({"collection": {"$in": table_names.split(',')}})

    collection = AuditLog().db()
    skip = max((page - 1) * per_page, 0)
    total_items = collection.aggregate(
        [
            {"$match": query},
            {"$sort": {sort_by: sort_order}},
            {"$skip": skip},
            {"$limit": per_page},
        ]
    )

    data = [AuditLog(**entity) for entity in total_items]
    total = collection.find(query, {"_id": 1}).count()

    return Paginator(data, page, per_page, total)
