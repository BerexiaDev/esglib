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


def create_reference_lookups(nested_fields: dict) -> list:
    """
    Generates a MongoDB aggregation pipeline for creating lookups and unwinding
    nested fields based on the provided configuration.

    This function constructs a series of MongoDB lookup operations to join
    data from different collections. If a field is not specified as a list,
    it unwinds the result to simplify access to the referenced document.

    Args:
        nested_fields (dict): A dictionary where `each key` represents a `field
            name` and its value is a dictionary containing:
            - "collection" (str): The name of the collection to join.
            - "is_list" (bool, optional): Indicates if the field is a list.
              Defaults to False.

    Returns:
        list: A list of pipeline stages to be used in a MongoDB aggregation
            operation.

    Example:
        nested_fields = {
            "author": {"collection": "users", "is_list": False},
            "tags": {"collection": "tags", "is_list": True},
        }
        pipeline = create_reference_lookups(nested_fields)

    Notes:
        - The function assumes that the local field names correspond to the
          foreign field `_id` in the specified collections.
        - The "$unwind" operation is used to flatten the resulting array
          when the field is not a list.
    """
    pipeline = []
    for field_name, field_info in nested_fields.items():
        collection_name = field_info["collection"]
        is_list = field_info.get("is_list", False)

        pipeline.append(
            {
                "$lookup": {
                    "from": collection_name,
                    "localField": field_name,
                    "foreignField": "_id",
                    "as": field_name,
                }
            }
        )

        if not is_list:
            pipeline.append(
                {
                    "$unwind": {
                        "path": f"${field_name}",
                        "preserveNullAndEmptyArrays": True,
                    }
                }
            )
    return pipeline
