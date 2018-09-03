import datetime

import dataclasses
from mongoengine import fields, connect
from salty_tickets import models
from salty_tickets.constants import FOLLOWER, LEADER, REGISTRATION_STATUSES, NEW
from salty_tickets.models.event import Event
from salty_tickets.models.order import Payment
from salty_tickets.models.personal_info import PersonInfo
from salty_tickets.models.products import BaseProduct, ProductRegistration
from salty_tickets.mongo_utils import fields_from_dataclass


@fields_from_dataclass(ProductRegistration, skip=['person', 'partner', 'registered_by', 'as_couple', 'details'])
class ProductRegistrationDocument(fields.Document):
    __meta__ = {
        'collection': 'product_registrations'
    }
    dance_role = fields.BaseField(choices=[LEADER, FOLLOWER])
    status = fields.BaseField(
        choices=REGISTRATION_STATUSES,
        default=NEW)
    person = fields.ReferenceField('RegistrationDocument', required=True)
    partner = fields.ReferenceField('RegistrationDocument', null=True)
    registered_by = fields.ReferenceField('RegistrationDocument', required=True)
    product_key = fields.StringField(required=True)
    event = fields.ReferenceField('EventDocument', required=True)

    def to_dataclass(self):
        model = self._to_dataclass()
        model.person = self.person.to_dataclass()
        model.registered_by = self.registered_by.to_dataclass()
        if self.partner:
            model.as_couple = True
            model.partner = self.partner.to_dataclass()
        return model


@fields_from_dataclass(BaseProduct, skip=['registrations', 'product_class', 'product_class_parameters'])
class EventProductDocument(fields.EmbeddedDocument):
    image_url = fields.URLField()

    product_class = fields.StringField(required=True)
    product_class_parameters = fields.DictField()

    @classmethod
    def from_dataclass(cls, model_dataclass):
        model_dict = dataclasses.asdict(model_dataclass)
        base_fields = [f.name for f in dataclasses.fields(BaseProduct)]
        kwargs = {f: model_dict.pop(f) for f in base_fields if f in model_dict}
        kwargs.pop('registrations')
        kwargs['product_class'] = model_dataclass.__class__.__name__
        kwargs['product_class_parameters'] = model_dict
        product_doc = cls(**kwargs)
        return product_doc

    def to_dataclass(self):
        kwargs = self.product_class_parameters
        model_class = getattr(models.products, self.product_class)
        model_fields = [f.name for f in dataclasses.fields(BaseProduct) if f.name not in ['registrations']]
        kwargs.update({f: getattr(self, f) for f in model_fields})
        product_model = model_class(**kwargs)
        return product_model


@fields_from_dataclass(Event, skip=['products'])
class EventDocument(fields.Document):
    __meta__ = {
        'collection': 'events',
        'indexes': ['key', 'start_date', 'active']
    }
    products = fields.MapField(fields.EmbeddedDocumentField(EventProductDocument))

    @classmethod
    def from_dataclass(cls, model_dataclass):
        event_doc = cls._from_dataclass(model_dataclass)
        event_doc.products = {p_key: EventProductDocument.from_dataclass(p)
                              for p_key, p in model_dataclass.products.items()}
        return event_doc

    def to_dataclass(self):
        event_model = self._to_dataclass()
        for p_key, prd in self.products.items():
            product_doc = prd.to_dataclass()
            event_model.products[p_key] = product_doc

        return event_model


# class RegistrationGroupDocument(fields.Document):
#     __meta__ = {
#         'collection': 'registration_groups'
#     }
#     type = fields.StringField()
#     parameters = fields.DictField()


@fields_from_dataclass(PersonInfo, skip=['event'])
class RegistrationDocument(fields.Document):
    __meta__ = {
        'collection': 'person_registrations'
    }
    event = fields.ReferenceField(EventDocument)


@fields_from_dataclass(Payment, skip=['payed_by', 'event'])
class PaymentDocument(fields.Document):
    __meta__ = {
        'collection': 'payments'
    }
    date = fields.DateTimeField(null=False, default=datetime.datetime.utcnow)
    payed_by = fields.ReferenceField(RegistrationDocument)
    event = fields.ReferenceField(EventDocument)


class TicketsDAO:
    def __init__(self):
        connect(host='mongomock://localhost')

    def get_event_by_key(self, key, get_registrations=True):
        event_doc = EventDocument.objects(key=key).first()
        if event_doc is None:
            return None

        event_model = event_doc.to_dataclass()
        if get_registrations:
            for product_key in event_model.products:
                registrations = self.get_registrations_for_product(event_doc, product_key)
                event_model.products[product_key].registrations = registrations

        return event_model

    def get_registrations_for_product(self, event, product):
        filter = {}
        if isinstance(product, str):
            filter['product_key'] = product
        else:
            filter['product_key'] = product.key

        if isinstance(event, str):
            filter['event__key'] = event
        elif event.id:
            filter['event'] = event.id
        else:
            raise ValueError(f'Invalid event argument: {event}')

        return [r.to_dataclass()
                for r in ProductRegistrationDocument.objects(**filter).all()]

    def create_event(self, event_model):
        event_doc = EventDocument.from_dataclass(event_model)
        event_doc.save()
