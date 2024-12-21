
def build_filters(filters):
    """
    Converts the filters object into a MongoDB query.
    
    :param filters: Array containing filter information.
    :return: MongoDB query as a dictionary.
    """
    mongo_query = {}

    for filter_item in filters:
        # Extract filter components
        table_name, field_info = filter_item.get("field", [None, {}])
        field_code = field_info.get("code", None)
        field_type = field_info.get("type", None)
        operator = filter_item.get('operator', None)
        value = filter_item.get('value', None)

        if not table_name:
            raise ValueError("No table name")
        if not field_code:
            raise ValueError("No columns name")
        if not field_type:
            raise ValueError("No field type")
        if not operator:
            raise ValueError("No operator")
        if value != 0 and not value:  # Allow 0 as a valid value
            raise ValueError("No value provided.")

        # Handle date-specific operators
        if operator in ["BEFORE", "AFTER"]:
            if not isinstance(value, (str)):
                raise ValueError(f"Value for '{operator}' operator must be a date string.")

            if operator == "BEFORE":
                mongo_query[field_code] = {"$lt": value}
            elif operator == "AFTER":
                mongo_query[field_code] = {"$gt": value}

        elif operator == "EQUALS":
            mongo_query[field_code] = value
        elif operator == "NOT EQUALS":
            mongo_query[field_code] = {"$ne": value}
        elif operator == "CONTAINS":
            if not isinstance(value, str):
                raise ValueError("Value for 'CONTAINS' operator must be a string.")
            mongo_query[field_code] = {"$regex": value, "$options": "i"}  
        elif operator == "GREATER THAN":
            mongo_query[field_code] = {"$gt": value}
        elif operator == "LESS THAN":
            mongo_query[field_code] = {"$lt": value}
        else:
            raise ValueError(f"Unsupported operator: {operator}")

    return mongo_query