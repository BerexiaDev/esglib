import uuid


def generate_id():
    return uuid.uuid4().hex.upper()


def build_advanced_filter(filters: dict) -> dict:
    """
    Build an advanced filter dictionary for MongoDB queries.

    Args:
        filters (dict): A dictionary containing the filters.

    Returns:
        dict: A MongoDB-compatible filter dictionary.

    Example:
        >>> filters = {
        ...     "status": "active",        # String exact match
        ...     "price": (100, 500),       # Range filter ($100 to $500)
        ...     "tags": ["new", "sale"],   # "In" filter
        ...     "stock": 20                # Exact match
        ... }
        >>> build_advanced_filter(filters)
        {
            "status": "active",
            "price": {"$gte": 100, "$lte": 500},
            "tags": {"$in": ["new", "sale"]},
            "stock": 20
        }
    """
    query = {}
    for key, value in filters.items():
        if isinstance(value, tuple) and len(value) == 2:
            # For range filters (e.g., price between two values)
            query[key] = {"$gte": value[0], "$lte": value[1]}
        elif isinstance(value, list):
            # For "in" type filters
            query[key] = {"$in": value}
        else:
            # Default exact match
            query[key] = value
    return query
