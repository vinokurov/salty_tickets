import datetime

import dataclasses
from mongoengine import fields, connect
from salty_tickets import models
from salty_tickets.models.event import Event
from salty_tickets.models.products import BaseProduct, ProductRegistration
from salty_tickets.mongo_utils import fields_from_dataclass


@fields_from_dataclass(ProductRegistration, skip=['registration'])
class ProductRegistrationDocument(fields.EmbeddedDocument):
    full_name = fields.StringField()
    email = fields.EmailField()
    dance_role = fields.BaseField(choices=['leader', 'follower'])
    as_couple = fields.BooleanField(default=False)
    status = fields.BaseField(choices=['accepted', 'waiting', 'cancelled', 'new'], default='new')
    registration = fields.ReferenceField('RegistrationDocument')
    #
    # def to_model_short(self):
    #     return mongo_to_dataclass(self, ProductRegistration, skip_fields=['registration'])


@fields_from_dataclass(BaseProduct, skip=['registrations', 'product_class', 'product_class_parameters'])
class EventProductDocument(fields.EmbeddedDocument):
    name = fields.StringField(required=True)
    key = fields.StringField(required=True)
    info = fields.StringField()
    max_available = fields.IntField(min_value=0, default=0)
    base_price = fields.DecimalField(default=0)
    image_url = fields.URLField()

    product_class = fields.StringField(required=True)
    product_class_parameters = fields.DictField()
    tags = fields.ListField(fields.StringField())

    registrations = fields.EmbeddedDocumentListField(ProductRegistrationDocument)

    @classmethod
    def from_dataclass(cls, model_dataclass):
        model_dict = dataclasses.asdict(model_dataclass)
        registrations = model_dict.pop('registrations')
        base_fields = [f.name for f in dataclasses.fields(BaseProduct)]
        kwargs = {f: model_dict.pop(f) for f in base_fields}
        kwargs['product_class'] = model_dataclass.__class__.__name__
        kwargs['product_class_parameters'] = model_dict
        product_doc = cls(**kwargs)
        return product_doc

    def to_dataclass(self):
        kwargs = self.product_class_parameters
        model_class = getattr(models, self.product_class)
        model_fields = [f.name for f in dataclasses.fields(BaseProduct) if f.name not in ['registrations']]
        kwargs.update({f: getattr(self, f) for f in model_fields})
        product_model = model_class(**kwargs)
        for registration in self.registrations:
            product_model.registrations.append(registration.to_model_short())
        return product_model


@fields_from_dataclass(Event, skip=['products'])
class EventDocument(fields.Document):
    __meta__ = {
        'collection': 'events',
        'indexes': ['key', 'start_date', 'active']
    }
    products = fields.EmbeddedDocumentListField(EventProductDocument)
    pricing_rules = fields.GenericEmbeddedDocumentField()

    @classmethod
    def from_dataclass(cls, model_dataclass):
        event_doc = cls._from_dataclass(model_dataclass)
        for product_model in model_dataclass.products:
            event_doc.products.append(EventProductDocument.from_model(product_model))
        return event_doc

    def to_dataclass(self):
        event_model = self._to_dataclass()
        for product in self.products:
            event_model.products.append(product.to_model())
        return event_model


class RegistrationGroupDocument(fields.Document):
    __meta__ = {
        'collection': 'registration_groups'
    }
    type = fields.StringField()
    parameters = fields.DictField()


class RegistrationDocument(fields.Document):
    __meta__ = {
        'collection': 'registrations'
    }
    full_name = fields.StringField(required=True)
    email = fields.EmailField(required=True)
    comment = fields.MultiLineStringField()
    registered_datetime = fields.DateTimeField(null=False, default=datetime.datetime.utcnow)

    location = fields.DictField()

    event = fields.ReferenceField(EventDocument)
    product_keys = fields.ListField(fields.StringField())
    registration_groups = fields.ListField(fields.ReferenceField(RegistrationGroupDocument))


class PurchaseItemDocument(fields.EmbeddedDocument):
    name = fields.StringField(required=True)
    product_key = fields.StringField()
    parameters = fields.DictField()
    price = fields.DecimalField(default=0)


class PurchasePaymentDocument(fields.EmbeddedDocument):
    date = fields.DateTimeField(null=False, default=datetime.datetime.utcnow)

    price = fields.DecimalField()
    transaction_fee = fields.DecimalField()
    total_amount = fields.DecimalField()

    success = fields.BooleanField()
    stripe_details = fields.GenericEmbeddedDocumentField()


class PurchaseDocument(fields.EmbeddedDocument):
    date = fields.DateTimeField(null=False, default=datetime.datetime.utcnow)
    purchase_items = fields.EmbeddedDocumentListField(PurchaseItemDocument)
    payments = fields.EmbeddedDocumentListField(PurchasePaymentDocument)


class OrderDocument(fields.Document):
    __meta__ = {
        'collection': 'orders'
    }
    event = fields.ReferenceField(EventDocument)
    full_name = fields.StringField()
    email = fields.EmailField()

    total_price = fields.DecimalField()
    total_paid = fields.DecimalField()

    registrations = fields.ListField(fields.ReferenceField(RegistrationDocument))
    purchases = fields.EmbeddedDocumentListField(PurchaseDocument)


class TicketsDAO:
    def get_event_by_key(self, key):
        event_doc = EventDocument.objects(key=key).first()
        if event_doc is not None:
            return event_doc.to_model()

    def create_event(self, event_model):
        event_doc = EventDocument.from_model(event_model)
        event_doc.save()
