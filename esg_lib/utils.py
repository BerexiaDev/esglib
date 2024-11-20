import uuid
import inject
from flask_pymongo import PyMongo

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



def fetch_objectives_with_details(
        objective_ids:str,
        objective_table="objectives",
        engagement_table="engagements",
        axe_table="axes",
    ) -> dict:
    """
    Retrieves a list of objectives by their IDs, along with related engagement 
    and axe details, formatted as a dictionary.

    Args:
        objective_ids (list): List of objective IDs to retrieve.
        objective_table (str): Name of the objectives collection in the database. 
                               Defaults to "objectives".
        engagement_table (str): Name of the engagements collection in the database. 
                                Defaults to "engagements".
        axe_table (str): Name of the axes collection in the database. 
                         Defaults to "axes".

    Returns:
        dict: A dictionary containing the objectives with engagement and axe details.
        
    Example:
        >>> fetch_objectives_with_details(["1D7258ECA93B45D9B2E701B071E65DF2", "949BDE53560B454D8F7B039A08B2A10F"])
        {
            "1D7258ECA93B45D9B2E701B071E65DF2":{
                "_id":"1D7258ECA93B45D9B2E701B071E65DF2",
                "name":"obj1",
                "engagement":{
                    "_id":"AF9B5C8F2F994AD39848AA483F8A27F9",
                    "name":"eng1"
                },
                "axe":{
                    "_id":"31D95D95B03F43C5A0F235A354525D53",
                    "name":"ax1"
                }
            },
            "949BDE53560B454D8F7B039A08B2A10F":{
                "_id":"949BDE53560B454D8F7B039A08B2A10F",
                "name":"obj2",
                "engagement":{
                    "_id":"079C9B751C464A7984C4E1210EA7EA8C",
                    "name":"eng2"
                },
                "axe":{
                    "_id":"20D7ADC5B53F4466B0063A018A2B2696",
                    "name":"ax2"
                }
            }
        }  
    """
    db = inject.instance(PyMongo).db
    objectives_collection = db[objective_table]
    engagements_collection = db[engagement_table]
    axes_collection = db[axe_table]

    objectives = list(objectives_collection.find({"_id": {"$in": objective_ids}}))

    engagement_ids = {obj["engagement"] for obj in objectives if "engagement" in obj}
    axe_ids = {obj["axe"] for obj in objectives if "axe" in obj}

    engagements = list(engagements_collection.find({"_id": {"$in": list(engagement_ids)}}))
    axes = list(axes_collection.find({"_id": {"$in": list(axe_ids)}}))

    engagement_lookup = {eng["_id"]: eng for eng in engagements}
    axe_lookup = {ax["_id"]: ax for ax in axes}

    return {
        obj["_id"]: {
            "_id": obj["_id"],
            "name": obj.get("name"),
            "engagement": (
                {
                    "_id": obj["engagement"],
                    "name": engagement_lookup.get(obj["engagement"], {}).get(
                        "name"
                    ),
                }
                if "engagement" in obj
                else None
            ),
            "axe": (
                {
                    "_id": obj["axe"],
                    "name": axe_lookup.get(obj["axe"], {}).get("name"),
                }
                if "axe" in obj
                else None
            ),
        }
        for obj in objectives
    }
