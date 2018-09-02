from datetime import datetime
from decimal import Decimal
from typing import List, Dict

from dataclasses import dataclass
from salty_tickets.mongo_utils import fields_from_dataclass
from mongoengine import fields


def test_fields_from_dataclass():
    @dataclass
    class MyDataClass:
        s: str
        i: int
        f: float
        b: bool
        d: datetime
        dc: Decimal
        # l: list

    @fields_from_dataclass(MyDataClass)
    class MyMongoDoc(fields.Document):
        pass

    kwargs = dict(s='ss', i=1, f=0.5, b=True, d=datetime(2018, 8, 27, 12, 35), dc=Decimal('0.1'))

    my_doc = MyMongoDoc(**kwargs)
    assert isinstance(my_doc, MyMongoDoc)

    my_dataclass = my_doc.to_dataclass()
    assert MyDataClass(**kwargs) == my_dataclass

    assert my_doc.to_json() == MyMongoDoc.from_dataclass(my_dataclass).to_json()


def test_fields_from_dataclass_required_fields():
    @dataclass
    class MyDataClass:
        s: str
        i: int
        f: float = 0
        b: bool = False

    @fields_from_dataclass(MyDataClass)
    class MyMongoDoc(fields.Document):
        pass

    assert MyMongoDoc.s.required
    assert MyMongoDoc.i.required
    assert not MyMongoDoc.f.required
    assert not MyMongoDoc.b.required


def test_fields_from_dataclass_extra_fields():
    @dataclass
    class MyDataClass:
        s: str
        b: bool

    @fields_from_dataclass(MyDataClass)
    class MyMongoDoc(fields.Document):
        i = fields.IntField(default=10)
        s = fields.EmailField()

    assert isinstance(MyMongoDoc.s, fields.EmailField)

    kwargs = dict(s='aa@gmail.com', b=True)
    doc = MyMongoDoc(**kwargs)
    assert doc.i == 10

    dc = MyDataClass(**kwargs)
    assert doc.to_json() == MyMongoDoc.from_dataclass(dc).to_json()
    assert doc.to_dataclass() == dc


# def test_list():
#     @dataclass
#     class MyDataClass:
#         li: List[str]
#
#     @fields_from_dataclass(MyDataClass)
#     class MyMongoDoc(fields.Document):
#         s = fields.StringField()
#
#     assert MyMongoDoc.li == fields.ListField(required=True)


def test_simple_dict_list():
    @dataclass
    class MyDataClass:
        di: Dict
        li_1: List
        li_a: List
        li_li: List

    @fields_from_dataclass(MyDataClass)
    class MyMongoDoc(fields.Document):
        pass

    assert isinstance(MyMongoDoc.di, fields.DictField)
    assert MyMongoDoc.di.required

    kwargs = dict(di={'a': 1, 'b': [1, 2], 'd': {'c': 'x'}},
                  li_1=[1, 2, 3],
                  li_a=['a', 'b', 'c'],
                  li_li=[[1, 2], ['a', 'b'], [], [None]])
    dtcl = MyDataClass(**kwargs)
    doc = MyMongoDoc(**kwargs)

    assert doc.di == dtcl.di
    assert doc.li_1 == dtcl.li_1
    assert doc.li_a == dtcl.li_a
    assert doc.li_li == dtcl.li_li
    assert MyMongoDoc.from_dataclass(dtcl).to_json() == doc.to_json()
    assert doc.to_dataclass() == dtcl
