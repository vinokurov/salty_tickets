import datetime
from typing import List

import dataclasses
from mongoengine import fields, connect
from salty_tickets import models
from salty_tickets.constants import FOLLOWER, LEADER, REGISTRATION_STATUSES, NEW
from salty_tickets.models.event import Event
from salty_tickets.models.registrations import Payment, PersonInfo, ProductRegistration
from salty_tickets.models.products import BaseProduct
from salty_tickets.mongo_utils import fields_from_dataclass


@fields_from_dataclass(ProductRegistration, skip=['person', 'partner', 'registered_by', 'as_couple', 'details'])
class ProductRegistrationDocument(fields.Document):
    __meta__ = {
        'collection': 'product_registrations'
    }
    dance_role = fields.BaseField(choices=[LEADER, FOLLOWER], null=True)
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


@fields_from_dataclass(Event, skip=['products', 'pricing_rules'])
class EventDocument(fields.Document):
    __meta__ = {
        'collection': 'events',
        'indexes': ['key', 'start_date', 'active']
    }
    key = fields.StringField()
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

    def get_event_by_key(self, key, get_registrations=True) -> Event:
        event_doc = EventDocument.objects(key=key).first()
        if event_doc is None:
            return None

        event_model = event_doc.to_dataclass()
        if get_registrations:
            for product_key in event_model.products:
                registrations = self.get_registrations_for_product(event_doc, product_key)
                event_model.products[product_key].registrations = registrations

        return event_model

    def get_registrations_for_product(self, event, product) -> List[ProductRegistration]:
        filter = {
            'product_key': self._get_product_key(product),
            'event': self._get_event_doc(event)
        }

        items = ProductRegistrationDocument.objects(**filter).all()
        return [r.to_dataclass() for r in items]

    def create_event(self, event_model):
        event_doc = EventDocument.from_dataclass(event_model)
        event_doc.save()

    def _get_event_doc(self, event):
        if isinstance(event, str):
            return EventDocument.objects(key=event).first()
        elif hasattr(event, 'id') and event.id:
            return EventDocument.objects(id=event.id).first()
        else:
            raise ValueError(f'Invalid event argument: {event}')

    def _get_product_key(self, product):
        if isinstance(product, str):
            return product
        else:
            return product.key

    def _get_or_create_new_person(self, person, event):
        if not hasattr(person, 'id'):
            self.add_person(person, event)
        return RegistrationDocument.objects(id=person.id).first()

    def add_person(self, person: PersonInfo, event: Event):
        if hasattr(person, 'id'):
            raise ValueError(f'Person already exists: {person}')
        else:
            person_doc = RegistrationDocument.from_dataclass(person)
            person_doc.event = self._get_event_doc(event)
            person_doc.save()
            person.id = person_doc.id

    def add_registration(self, registration: ProductRegistration, event: Event):
        if hasattr(registration, 'id'):
            raise ValueError(f'Registration already exists: {registration}')

        registration_doc = ProductRegistrationDocument.from_dataclass(registration)
        registration_doc.event = self._get_event_doc(event)
        registration_doc.person = self._get_or_create_new_person(registration.person, event)
        registration_doc.registered_by = self._get_or_create_new_person(registration.registered_by, event)
        if registration.partner:
            registration_doc.partner = self._get_or_create_new_person(registration.partner, event)
        registration_doc.save()
        registration.id = registration_doc.id

