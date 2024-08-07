import inject
from flask_pymongo import PyMongo
from esg_lib.convertible import default_field

from esg_lib.utils import generate_id


class Document:
    IGNORED_FIELDS = []

    __TABLE__ = None
    id: str = default_field()

    def db(self):
        mongo = inject.instance(PyMongo)
        return mongo.db[self.__TABLE__]

    def save(self):
        _id = self.id
        if not _id:
            _id = generate_id()
        save_dict = self.to_dict(ignore_date_time=True)
        save_dict.pop("id", None)
        save_dict["_id"] = _id
        self.id = self.db().save(save_dict)
        return self

    def save_all(self, items, **kwargs):
        kwargs = kwargs or {}
        cls = type(self)
        item_instances = [cls.from_dict({**item, **kwargs}) for item in items]
        items = [{"_id": generate_id(), **item.to_dict(ignore_date_time=True)} for item in item_instances]
        [item.pop("id", None) for item in items]
        self.db().insert_many(items)

    def load(self, query=None):
        if not query:
            query = {"_id": self.id}
        cls = type(self)
        return cls.from_dict(self.db().find_one(query))

    def delete(self, query=None):
        if self.id:
            if not query:
                query = {"_id": self.id}
            self.db().remove(query)
        return self

    @classmethod
    def get_all(cls, query={}):
        return [cls.from_dict(r) for r in cls().db().find(query)]

    @classmethod
    def drop(cls):
        return cls().db().drop()

    @classmethod
    def delete_all(cls, query):
        if query:
            cls().db().delete_many(query)
