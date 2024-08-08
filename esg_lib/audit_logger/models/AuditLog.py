from datetime import datetime
from esg_lib.document import Document
from esg_lib.convertible import convertibleclass, default_field, required_field
from esg_lib.convertible_utils import default_datetime_meta


@convertibleclass
class AuditLog(Document):
    __TABLE__ = "audit"

    id: str = default_field()
    collection: str = default_field()
    action: str = required_field()
    endpoint: str = required_field()
    user: dict = default_field()
    old_value: dict = default_field()
    new_value: dict = default_field()
    created_on: datetime = default_field(metadata=default_datetime_meta())
