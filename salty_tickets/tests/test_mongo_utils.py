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

    @fields_from_dataclass(MyDataClass)
    class MyMongoDoc(fields.Document):
        pass

    kwargs = dict(s='ss', i=1, f=0.5, b=True)

    my_doc = MyMongoDoc(**kwargs)
    assert isinstance(my_doc, MyMongoDoc)

    my_dataclass = my_doc.to_dataclass()
    assert MyDataClass(**kwargs) == my_dataclass

    assert my_doc.to_json() == MyMongoDoc.from_dataclass(my_dataclass).to_json()
