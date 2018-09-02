import datetime
from decimal import Decimal
from typing import List, Dict, Set

import dataclasses
from mongoengine import fields


def mongo_to_dataclass(mongo_model, dataclass_class, skip_fields=None):
    if skip_fields is None:
        skip_fields = []

    model_fields = [f.name for f in dataclasses.fields(dataclass_class) if f.name not in skip_fields]
    kwargs = {f: mongo_model[f] for f in model_fields}
    return dataclass_class(**kwargs)


def dataclass_to_mongo(dataclass_inst, mongo_class, skip_fields=None):
    model_dict = dataclasses.asdict(dataclass_inst)

    if skip_fields is not None:
        model_dict = {k: v for k, v in model_dict.items() if k not in skip_fields}

    return mongo_class(**model_dict)


def fields_from_dataclass(dataclass_class, skip=None):
    if skip is None:
        skip = []

    def class_rebuilder(mongo_class):
        dataclass_fields = dataclasses.fields(dataclass_class)
        field_mapping = {
            str: fields.StringField,
            int: fields.IntField,
            float: fields.FloatField,
            bool: fields.BooleanField,
            datetime.datetime: fields.DateTimeField,
            Decimal: fields.DecimalField,
            Dict: fields.DictField,
            List: fields.ListField,
            Set: fields.ListField,
        }

        original_fields = mongo_class.__dict__.copy()
        for field in dataclass_fields:
            if field.name not in skip and field.name not in original_fields:
                kwargs = dict(db_field=field.name)
                if field.default == dataclasses.MISSING and field.default_factory == dataclasses.MISSING:
                    kwargs['required'] = True
                if field.type in field_mapping:
                    field_obj = field_mapping[field.type](**kwargs)
                    field_obj.name = field.name
                    field_obj.owner_document = mongo_class
                    setattr(mongo_class, field.name, field_obj)
                    mongo_class._fields[field.name] = field_obj
                    mongo_class._fields_ordered += (field.name,)
                    mongo_class._db_field_map[field.name] = field.name
                    mongo_class._reverse_db_field_map[field.name] = field.name
                else:
                    print(f'missing mapping for field type {field.type}')

        def _from_dataclass(cls, dataclass_inst):
            return dataclass_to_mongo(dataclass_inst, cls, skip)

        def _to_dataclass(self):
            return mongo_to_dataclass(self, dataclass_class, skip)

        setattr(mongo_class, '_from_dataclass', classmethod(_from_dataclass))
        setattr(mongo_class, '_to_dataclass', _to_dataclass)

        if 'from_dataclass' not in original_fields:
            setattr(mongo_class, 'from_dataclass', classmethod(_from_dataclass))

        if 'to_dataclass' not in original_fields:
            setattr(mongo_class, 'to_dataclass', _to_dataclass)

        return mongo_class

    return class_rebuilder
