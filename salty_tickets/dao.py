import datetime
import typing
from typing import List

import dataclasses
from bson import ObjectId
from mongoengine import fields, connect
from salty_tickets import models
from salty_tickets.constants import FOLLOWER, LEADER, REGISTRATION_STATUSES, NEW
from salty_tickets.models.event import Event
from salty_tickets.models.registrations import Payment, PersonInfo, ProductRegistration, PaymentStripeDetails
from salty_tickets.models.products import BaseProduct
from salty_tickets.utils.mongo_utils import fields_from_dataclass


@fields_from_dataclass(ProductRegistration, skip=['person', 'partner', 'registered_by', 'as_couple', 'details'])
class ProductRegistrationDocument(fields.Document):
    meta = {
        'collection': 'product_registrations'
    }
    dance_role = fields.BaseField(choices=[LEADER, FOLLOWER], null=True)
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
    meta = {
        'collection': 'events',
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
#     int_id = fields.SequenceField()
#
#     def to_dataclass(self):
#         model = self._to_dataclass()
#         model.int_id = self.int_id
#         return model

@fields_from_dataclass(PersonInfo, skip=['event'])
class RegistrationDocument(fields.Document):
    meta = {
        'collection': 'person_registrations',
    }
    event = fields.ReferenceField(EventDocument)
    int_id = fields.SequenceField()

    def to_dataclass(self):
        model = self._to_dataclass()
        model.int_id = self.int_id
        return model


@fields_from_dataclass(PaymentStripeDetails)
class PaymentStripeDetailsDocument(fields.EmbeddedDocument):
    pass


@fields_from_dataclass(Payment, skip=['paid_by', 'event', 'registrations', 'extra_registrations'])
class PaymentDocument(fields.Document):
    meta = {
        'collection': 'payments'
    }
    date = fields.DateTimeField(null=False, default=datetime.datetime.utcnow)
    paid_by = fields.ReferenceField(RegistrationDocument)
    event = fields.ReferenceField(EventDocument)
    registrations = fields.ListField(fields.ReferenceField(ProductRegistrationDocument))
    extra_registrations = fields.ListField(fields.ReferenceField(ProductRegistrationDocument))
    stripe = fields.EmbeddedDocumentField(PaymentStripeDetailsDocument)
    # int_id = fields.SequenceField()

    def to_dataclass(self) -> Payment:
        model = self._to_dataclass(paid_by=self.paid_by.to_dataclass())
        model.registrations = [r.to_dataclass() for r in self.registrations]
        model.extra_registrations = [r.to_dataclass() for r in self.extra_registrations]
        if self.stripe:
            model.stripe = self.stripe.to_dataclass()
        # model.int_id = self.int_id
        return model

    @classmethod
    def from_dataclass(cls, model):
        doc = cls._from_dataclass(model)
        if doc.stripe is not None:
            doc.stripe = PaymentStripeDetailsDocument.from_dataclass(model.stripe)
        return doc


class TicketsDAO:
    def __init__(self, host=None):
        if host is None:
            host = 'mongomock://localhost'

        connect(host=host)
        # from salty_tickets.utils.demo_db import salty_recipes
        # salty_recipes(self)

    def get_event_by_key(self, key, get_registrations=True) -> typing.Optional[Event]:
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
        filters = {
            'product_key': self._get_product_key(product),
            'event': self._get_event_doc(event)
        }

        items = ProductRegistrationDocument.objects(**filters).all()
        return [r.to_dataclass() for r in items]

    def create_event(self, event_model):
        event_doc = EventDocument.from_dataclass(event_model)
        event_doc.save()

    def _get_event_doc(self, event) -> EventDocument:
        if isinstance(event, str):
            return EventDocument.objects(key=event).first()
        elif hasattr(event, 'id') and event.id:
            return EventDocument.objects(id=event.id).first()
        else:
            raise ValueError(f'Invalid event argument: {event}')

    def _get_product_key(self, product) -> str:
        if isinstance(product, str):
            return product
        else:
            return product.key

    def _get_or_create_new_person(self, person, event) -> RegistrationDocument:
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

    def add_registration(self, registration: ProductRegistration, event):
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

    def add_payment(self, payment: Payment, event, register=False):
        if hasattr(payment, 'id'):
            raise ValueError(f'Payment already exists: {payment}')
        print(payment)
        payment_doc = PaymentDocument.from_dataclass(payment)
        payment_doc.event = self._get_event_doc(event)
        payment_doc.paid_by = self._get_or_create_new_person(payment.paid_by, event)
        for reg in payment.registrations:
            if not hasattr(reg, 'id'):
                if not register:
                    raise ValueError(f'Registrations need to be added first: {reg}')
                else:
                    self.add_registration(reg, event)
            payment_doc.registrations.append(reg.id)

        payment_doc.extra_registrations = [r.id for r in payment.extra_registrations]

        payment_doc.save()
        payment.id = payment_doc.id

    @staticmethod
    def _get_doc(doc_class, model):
        if isinstance(model, doc_class):
            return model
        elif hasattr(model, 'id'):
            return doc_class.objects(id=model.id).first()
        elif isinstance(model, ObjectId):
            return doc_class.objects(id=model).first()
        elif hasattr(doc_class, 'key') and isinstance(model, str):
            return doc_class.objects(key=model).first()
        else:
            raise ValueError(f'Can\'t find {doc_class} by {model}')

    def get_payments_by_person(self, event, person: PersonInfo) -> List[Payment]:
        event_doc = self._get_doc(EventDocument, event)
        person_doc = self._get_doc(RegistrationDocument, person)
        payment_docs = PaymentDocument.objects(event=event_doc, paid_by=person_doc).all()
        return [p.to_dataclass() for p in payment_docs]

    def get_payment_by_registration(self, registration):
        if hasattr(registration, 'id'):
            payment_doc = PaymentDocument.objects.filter(registrations__contains=registration.id).first()
            if payment_doc:
                return payment_doc.to_dataclass()

    def query_registrations(self, event, person: PersonInfo=None, paid_by: PersonInfo=None,
                            partner: PersonInfo=None, product=None) -> List[ProductRegistration]:
        filters = {'event': self._get_doc(EventDocument, event)}
        if person is not None:
            filters['person'] = self._get_doc(RegistrationDocument, person)
        if paid_by is not None:
            filters['paid_by'] = self._get_doc(RegistrationDocument, paid_by)
        if partner is not None:
            filters['partner'] = self._get_doc(RegistrationDocument, partner)
        if product is not None:
            filters['product_key'] = self._get_product_key(product)

        return [r.to_dataclass() for r in ProductRegistrationDocument.objects(**filters).all()]

    def _update_doc(self, doc_class, model, **kwargs):
        saved_model_doc = self._get_doc(doc_class, model)
        saved_model = saved_model_doc.to_dataclass()
        need_save = False
        for field in dataclasses.fields(model):
            if field.name not in doc_class._skip_fields:
                if getattr(model, field.name) != getattr(saved_model, field.name):
                    value = getattr(model, field.name)
                    if dataclasses.is_dataclass(value):
                        value_mongo_cls = saved_model_doc._fields[field.name].document_type
                        value_ = value_mongo_cls.from_dataclass(value)
                        setattr(saved_model_doc, field.name, value_)
                    else:
                        setattr(saved_model_doc, field.name, value)
                    need_save = True
            # else:
            #     print(f'{self._update_doc}: skipping field: {field.name} = {field}')
        for k, v in kwargs.items():
            setattr(saved_model_doc, k, v)
            need_save = True
        if need_save:
            saved_model_doc.save()
            model = saved_model_doc.to_dataclass()

    def update_person(self, person: PersonInfo):
        self._update_doc(RegistrationDocument, person)

    def update_registration(self, registration: ProductRegistration):
        registration_0 = self.get_product_registration_by_id(registration.id)
        extra_updates = {}
        event = ProductRegistrationDocument.objects(id=registration.id).first().event.key
        if registration.person != registration_0.person:
            extra_updates['person'] = self._get_or_create_new_person(registration.person, event)
        if registration.registered_by != registration_0.registered_by:
            extra_updates['registered_by'] = self._get_or_create_new_person(registration.registered_by, event)
        if registration.partner != registration_0.partner:
            extra_updates['partner'] = self._get_or_create_new_person(registration.partner, event)

        self._update_doc(ProductRegistrationDocument, registration, **extra_updates)

    def update_payment(self, payment: Payment):
        self._update_doc(PaymentDocument, payment)

    def mark_registrations_as_couple(self,
                                     registration_1: ProductRegistration,
                                     registration_2: ProductRegistration):
        registration_1.partner = registration_2.person
        registration_2.partner = registration_1.person
        self.update_registration(registration_1)
        self.update_registration(registration_2)

    def get_payment_by_id(self, payment_id) -> Payment:
        doc = PaymentDocument.objects(**id_filter(payment_id)).first()
        if doc:
            return doc.to_dataclass()

    def get_payment_event(self, payment: Payment, get_registrations=True) -> Event:
        payment_doc = PaymentDocument.objects(id=payment.id).first()
        if payment_doc:
            return self.get_event_by_key(payment_doc.event.key, get_registrations=get_registrations)

    def get_person_by_id(self, object_id) -> PersonInfo:
        doc = RegistrationDocument.objects(**id_filter(object_id)).first()
        if doc:
            return doc.to_dataclass()

    def get_payments_by_event(self, event: Event) -> List[Payment]:
        docs = PaymentDocument.objects(event=event.id).all()
        if docs:
            return [d.to_dataclass() for d in docs]

    def get_product_registration_by_id(self, object_id) -> ProductRegistration:
        doc = ProductRegistrationDocument.objects(**id_filter(object_id)).first()
        if doc:
            return doc.to_dataclass()


def id_filter(object_id):
    if isinstance(object_id, ObjectId):
        return {'id': object_id}
    elif isinstance(object_id, str):
        return {'id': ObjectId(object_id)}
    elif isinstance(object_id, int):
        return {'int_id': object_id}
    else:
        raise ValueError(f'Unsupported id type: {object_id} {type(object_id)}')
