import datetime
import typing
from typing import List

import dataclasses
from bson import ObjectId
from mongoengine import fields, connect
from salty_tickets import models
from salty_tickets.constants import FOLLOWER, LEADER
from salty_tickets.models.discounts import DiscountProduct, DiscountCode
from salty_tickets.models.event import Event
from salty_tickets.models.products import Product
from salty_tickets.models.registrations import Payment, Person, Registration, PaymentStripeDetails, Purchase, Discount, \
    RegistrationGroup
from salty_tickets.models.tickets import Ticket
from salty_tickets.utils.mongo_utils import fields_from_dataclass
from salty_tickets.utils.utils import timeit


@fields_from_dataclass(Registration, skip=['person', 'partner', 'registered_by', 'as_couple', 'details'])
class RegistrationDocument(fields.Document):
    meta = {
        'collection': 'registrations'
    }
    dance_role = fields.BaseField(choices=[LEADER, FOLLOWER], null=True)
    person = fields.ReferenceField('PersonDocument', required=True)
    partner = fields.ReferenceField('PersonDocument', null=True)
    registered_by = fields.ReferenceField('PersonDocument', required=True)
    ticket_key = fields.StringField(required=True)
    event = fields.ReferenceField('EventDocument', required=True)

    def to_dataclass(self):
        model = self._to_dataclass()
        model.person = self.person.to_dataclass()
        model.registered_by = self.registered_by.to_dataclass()
        if self.partner:
            model.partner = self.partner.to_dataclass()
        return model


@fields_from_dataclass(Purchase, skip=['person'])
class PurchaseDocument(fields.Document):
    meta = {
        'collection': 'purchases',
    }
    person = fields.ReferenceField('PersonDocument', required=True)

    def to_dataclass(self):
        model = self._to_dataclass()
        model.person = self.person.to_dataclass()
        return model


@fields_from_dataclass(Discount, skip=['person'])
class DiscountDocument(fields.EmbeddedDocument):
    person = fields.ReferenceField('PersonDocument', required=True)

    def to_dataclass(self):
        model = self._to_dataclass()
        model.person = self.person.to_dataclass()
        return model

    @classmethod
    def from_dataclass(cls, model: Discount):
        doc = cls._from_dataclass(model)
        doc.person = model.person.id
        return doc


@fields_from_dataclass(Ticket, skip=['registrations', 'ticket_class', 'ticket_class_parameters'])
class TicketDocument(fields.EmbeddedDocument):
    image_url = fields.URLField()

    ticket_class = fields.StringField(required=True)
    ticket_class_parameters = fields.DictField()

    @classmethod
    def from_dataclass(cls, model_dataclass):
        model_dict = dataclasses.asdict(model_dataclass)
        base_fields = [f.name for f in dataclasses.fields(Ticket)]
        kwargs = {f: model_dict.pop(f) for f in base_fields if f in model_dict}
        kwargs.pop('registrations')
        kwargs['ticket_class'] = model_dataclass.__class__.__name__
        kwargs['ticket_class_parameters'] = model_dict
        ticket_doc = cls(**kwargs)
        return ticket_doc

    def to_dataclass(self):
        kwargs = self.ticket_class_parameters
        model_class = getattr(models.tickets, self.ticket_class)
        model_fields = [f.name for f in dataclasses.fields(Ticket) if f.name not in ['registrations']]
        kwargs.update({f: getattr(self, f) for f in model_fields})
        ticket_model = model_class(**kwargs)
        return ticket_model


@fields_from_dataclass(Product)
class ProductDocument(fields.EmbeddedDocument):
    pass


@fields_from_dataclass(DiscountProduct, skip=['discount_product_class', 'discount_product_parameters'])
class DiscountProductDocument(fields.EmbeddedDocument):
    discount_product_class = fields.StringField(required=True)
    discount_product_parameters = fields.DictField()

    @classmethod
    def from_dataclass(cls, model_dataclass):
        model_dict = dataclasses.asdict(model_dataclass)
        base_fields = [f.name for f in dataclasses.fields(DiscountProduct)]
        kwargs = {f: model_dict.pop(f) for f in base_fields if f in model_dict}
        kwargs['discount_product_class'] = model_dataclass.__class__.__name__
        kwargs['discount_product_parameters'] = model_dict
        ticket_doc = cls(**kwargs)
        return ticket_doc

    def to_dataclass(self):
        kwargs = self.discount_product_parameters
        model_class = getattr(models.discounts, self.discount_product_class)
        model_fields = [f.name for f in dataclasses.fields(DiscountProduct)]
        kwargs.update({f: getattr(self, f) for f in model_fields})
        ticket_model = model_class(**kwargs)
        return ticket_model


@fields_from_dataclass(Event, skip=['tickets', 'merchandise', 'discount_products'])
class EventDocument(fields.Document):
    meta = {
        'collection': 'events',
    }
    key = fields.StringField()
    tickets = fields.MapField(fields.EmbeddedDocumentField(TicketDocument))
    products = fields.MapField(fields.EmbeddedDocumentField(ProductDocument))
    discount_products = fields.MapField(fields.EmbeddedDocumentField(DiscountProductDocument))

    @classmethod
    def from_dataclass(cls, model_dataclass):
        event_doc = cls._from_dataclass(model_dataclass)
        event_doc.tickets = {p_key: TicketDocument.from_dataclass(p)
                             for p_key, p in model_dataclass.tickets.items()}
        event_doc.products = {p_key: ProductDocument.from_dataclass(p)
                              for p_key, p in model_dataclass.products.items()}
        event_doc.discount_products = {p_key: DiscountProductDocument.from_dataclass(p)
                              for p_key, p in model_dataclass.discount_products.items()}
        return event_doc

    def to_dataclass(self):
        event_model = self._to_dataclass()
        for p_key, prd in self.tickets.items():
            ticket_doc = prd.to_dataclass()
            event_model.tickets[p_key] = ticket_doc

        for p_key, prd in self.products.items():
            product_doc = prd.to_dataclass()
            event_model.products[p_key] = product_doc

        for p_key, prd in self.discount_products.items():
            discount_product_doc = prd.to_dataclass()
            event_model.discount_products[p_key] = discount_product_doc

        return event_model


@fields_from_dataclass(RegistrationGroup, skip=['admin', 'members', 'event'])
class RegistrationGroupDocument(fields.Document):
    __meta__ = {
        'collection': 'registration_groups'
    }
    int_id = fields.SequenceField()
    event = fields.ReferenceField(EventDocument)
    admin = fields.ReferenceField('PersonDocument')
    members = fields.ListField(fields.ReferenceField('PersonDocument'))

    def to_dataclass(self) -> RegistrationGroup:
        model = self._to_dataclass()
        model.int_id = self.int_id
        if self.admin is not None:
            model.admin = self.admin.to_dataclass()
        model.members = [m.to_dataclass() for m in self.members]
        return model

    @classmethod
    def from_dataclass(cls, model: RegistrationGroup):
        doc = cls._from_dataclass(model)
        if model.admin is not None:
            doc.admin = model.admin.id
        if model.members:
            doc.members = [m.id for m in model.members]
        return doc


@fields_from_dataclass(Person, skip=['event'])
class PersonDocument(fields.Document):
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


@fields_from_dataclass(Payment, skip=['paid_by', 'event', 'registrations', 'purchases', 'discounts', 'extra_registrations'])
class PaymentDocument(fields.Document):
    meta = {
        'collection': 'payments'
    }
    date = fields.DateTimeField(null=False, default=datetime.datetime.utcnow)
    paid_by = fields.ReferenceField(PersonDocument)
    event = fields.ReferenceField(EventDocument)
    registrations = fields.ListField(fields.ReferenceField(RegistrationDocument))
    extra_registrations = fields.ListField(fields.ReferenceField(RegistrationDocument))
    purchases = fields.ListField(fields.ReferenceField(PurchaseDocument))
    discounts = fields.EmbeddedDocumentListField(DiscountDocument)
    stripe = fields.EmbeddedDocumentField(PaymentStripeDetailsDocument)
    # int_id = fields.SequenceField()

    def to_dataclass(self) -> Payment:
        model = self._to_dataclass(paid_by=self.paid_by.to_dataclass())
        model.registrations = [r.to_dataclass() for r in self.registrations]
        model.extra_registrations = [r.to_dataclass() for r in self.extra_registrations]
        model.purchases = [p.to_dataclass() for p in self.purchases]
        model.discounts = [p.to_dataclass() for p in self.discounts]
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


@fields_from_dataclass(DiscountCode)
class DiscountCodeDocument(fields.Document):
    meta = {
        'collection': 'discount_codes',
    }
    event = fields.ReferenceField(EventDocument)
    int_id = fields.SequenceField()

    def to_dataclass(self):
        model = self._to_dataclass()
        model.int_id = self.int_id
        return model


class TicketsDAO:
    def __init__(self, host=None):
        if host is None:
            host = 'mongomock://localhost'

        connect(host=host)
        # from salty_tickets.utils.demo_db import salty_recipes
        # salty_recipes(self)

    def get_event_by_key(self, event_key, get_registrations=True) -> typing.Optional[Event]:
        event_doc = self._get_event_doc(event_key)
        if event_doc is None:
            return None

        event = event_doc.to_dataclass()
        if get_registrations:
            registrations = self.query_registrations(event)
            for ticket_key in event.tickets:
                event.tickets[ticket_key].registrations = [r for r in registrations if r.ticket_key == ticket_key]

        return event

    def get_registrations_for_ticket(self, event: Event, ticket) -> List[Registration]:
        filters = {
            'ticket_key': self._get_ticket_key(ticket),
            'event': event.id,
        }

        items = RegistrationDocument.objects(**filters).select_related(3)
        return [r.to_dataclass() for r in items]

    def create_event(self, event_model):
        event_doc = EventDocument.from_dataclass(event_model)
        event_doc.save()
        event_model.id = event_doc.id

    def _get_event_doc(self, event) -> EventDocument:
        if isinstance(event, str):
            return EventDocument.objects(key=event).first()
        elif hasattr(event, 'id') and event.id:
            return EventDocument.objects(id=event.id).first()
        else:
            raise ValueError(f'Invalid event argument: {event}')

    def _get_event_id(self, event) -> EventDocument:
        if isinstance(event, str):
            return EventDocument.objects(key=event).first().id
        elif hasattr(event, 'id') and event.id:
            return event.id
        else:
            raise ValueError(f'Invalid event argument: {event}')

    def _get_ticket_key(self, ticket) -> str:
        if isinstance(ticket, str):
            return ticket
        else:
            return ticket.key

    def _get_or_create_new_person(self, person, event) -> PersonDocument:
        if not hasattr(person, 'id'):
            self.add_person(person, event)
        return PersonDocument.objects(id=person.id).first()

    def add_person(self, person: Person, event: Event):
        if hasattr(person, 'id'):
            raise ValueError(f'Person already exists: {person}')
        else:
            person_doc = PersonDocument.from_dataclass(person)
            person_doc.event = event.id
            person_doc.save()
            person.id = person_doc.id

    def add_registration(self, registration: Registration, event):
        if hasattr(registration, 'id'):
            raise ValueError(f'Registration already exists: {registration}')

        registration_doc = RegistrationDocument.from_dataclass(registration)
        registration_doc.event = event.id
        registration_doc.person = self._get_or_create_new_person(registration.person, event)
        registration_doc.registered_by = self._get_or_create_new_person(registration.registered_by, event)
        if registration.partner:
            registration_doc.partner = self._get_or_create_new_person(registration.partner, event)
        registration_doc.save()
        registration.id = registration_doc.id

    def add_purchase(self, purchase: Purchase, event):
        if hasattr(purchase, 'id'):
            raise ValueError(f'Purchase already exists: {purchase}')

        purchase_doc = PurchaseDocument.from_dataclass(purchase)
        purchase_doc.event = event.id
        purchase_doc.person = self._get_or_create_new_person(purchase.person, event)
        purchase_doc.save()
        purchase.id = purchase_doc.id

    @timeit
    def add_payment(self, payment: Payment, event: Event, register=False):
        if hasattr(payment, 'id'):
            raise ValueError(f'Payment already exists: {payment}')
        print(payment)
        payment_doc = PaymentDocument.from_dataclass(payment)
        payment_doc.event = event.id
        payment_doc.paid_by = self._get_or_create_new_person(payment.paid_by, event)
        for reg in payment.registrations:
            if not hasattr(reg, 'id'):
                if not register:
                    raise ValueError(f'Registrations need to be added first: {reg}')
                else:
                    self.add_registration(reg, event)
            payment_doc.registrations.append(reg.id)

        payment_doc.extra_registrations = [r.id for r in payment.extra_registrations]

        for prd in payment.purchases:
            if not hasattr(prd, 'id'):
                if not register:
                    raise ValueError(f'Purchases need to be added first: {reg}')
                else:
                    self.add_purchase(prd, event)
            payment_doc.purchases.append(prd.id)

        for discount in payment.discounts:
            payment_doc.discounts.append(DiscountDocument.from_dataclass(discount))

        payment_doc.discounts = [DiscountDocument.from_dataclass(d) for d in payment.discounts]

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

    def get_payments_by_person(self, event: Event, person: Person) -> List[Payment]:
        person_doc = self._get_doc(PersonDocument, person)
        payment_docs = PaymentDocument.objects(event=event.id, paid_by=person_doc).select_related(3)
        return [p.to_dataclass() for p in payment_docs]

    def get_payment_by_registration(self, registration):
        if hasattr(registration, 'id'):
            payment_doc = PaymentDocument.objects.filter(registrations__contains=registration.id).first()
            if payment_doc:
                return payment_doc.to_dataclass()

    def query_registrations(self, event: Event, person: Person=None, paid_by: Person=None,
                            partner: Person=None, ticket=None) -> List[Registration]:
        filters = {'event': self._get_event_id(event)}
        if person is not None:
            filters['person'] = self._get_doc(PersonDocument, person)
        if paid_by is not None:
            filters['paid_by'] = self._get_doc(PersonDocument, paid_by)
        if partner is not None:
            filters['partner'] = self._get_doc(PersonDocument, partner)
        if ticket is not None:
            filters['ticket_key'] = self._get_ticket_key(ticket)

        return [r.to_dataclass() for r in RegistrationDocument.objects(**filters).select_related(3)]

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

    def update_person(self, person: Person):
        self._update_doc(PersonDocument, person)

    def update_registration(self, registration: Registration):
        registration_0 = self.get_ticket_registration_by_id(registration.id)
        extra_updates = {}
        event = RegistrationDocument.objects(id=registration.id).first().event.key
        if registration.person != registration_0.person:
            extra_updates['person'] = self._get_or_create_new_person(registration.person, event)
        if registration.registered_by != registration_0.registered_by:
            extra_updates['registered_by'] = self._get_or_create_new_person(registration.registered_by, event)
        if registration.partner != registration_0.partner:
            extra_updates['partner'] = self._get_or_create_new_person(registration.partner, event)

        self._update_doc(RegistrationDocument, registration, **extra_updates)

    @timeit
    def update_payment(self, payment: Payment):
        self._update_doc(PaymentDocument, payment)

    def mark_registrations_as_couple(self, registration_1: Registration, registration_2: Registration):
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

    def get_person_by_id(self, object_id) -> Person:
        doc = PersonDocument.objects(**id_filter(object_id)).first()
        if doc:
            return doc.to_dataclass()

    def get_payments_by_event(self, event: Event) -> List[Payment]:
        docs = PaymentDocument.objects(event=event.id).select_related(3)
        if docs:
            return [d.to_dataclass() for d in docs]

    def get_ticket_registration_by_id(self, object_id) -> Registration:
        doc = RegistrationDocument.objects(**id_filter(object_id)).first()
        if doc:
            return doc.to_dataclass()

    def get_discount_code_by_id(self, object_id) -> Person:
        doc = DiscountCodeDocument.objects(**id_filter(object_id)).first()
        if doc:
            return doc.to_dataclass()

    def add_discount_code(self, event: Event, discount_code: DiscountCode):
        if hasattr(discount_code, 'id'):
            raise ValueError(f'Discount code already exists: {discount_code}')
        discount_code_doc = DiscountCodeDocument.from_dataclass(discount_code)
        discount_code_doc.event = event.id
        discount_code_doc.save()
        discount_code.id = discount_code_doc.id
        discount_code.int_id = discount_code_doc.int_id

    def increment_discount_code_usages(self, discount_code: DiscountCode, usages=1):
        if not hasattr(discount_code, 'id'):
            raise ValueError(f'Discount code isn`t saved: {discount_code}')
        discount_code_doc = DiscountCodeDocument.objects(**id_filter(discount_code.id)).first()
        discount_code_doc.times_used += usages
        discount_code_doc.save()
        discount_code.times_used = discount_code_doc.times_used

    def add_registration_group(self, event: Event, registration_group: RegistrationGroup):
        doc = RegistrationGroupDocument.from_dataclass(registration_group)
        doc.event = event.id
        doc.save()
        registration_group.id = doc.id
        registration_group.int_id = doc.int_id

    def check_registration_group_name_exists(self, event: Event, name: str) -> bool:
        res = RegistrationGroupDocument.objects(name=name, event=event.id).count()
        return res > 0

    def get_registration_group_by_id(self, object_id) -> RegistrationGroup:
        doc = RegistrationGroupDocument.objects(**id_filter(object_id)).first()
        if doc:
            return doc.to_dataclass()

    def add_registration_group_member(self, registration_group: RegistrationGroup, person: Person):
        if not hasattr(person, 'id'):
            raise ValueError('Person need to be saved first')
        if not hasattr(registration_group, 'id'):
            raise ValueError('Registration group need to be saved first')

        doc = RegistrationGroupDocument.objects(**id_filter(registration_group.id)).first()
        doc.members.append(person.id)
        doc.save()
        registration_group.members.append(person)


def id_filter(object_id):
    if isinstance(object_id, ObjectId):
        return {'id': object_id}
    elif isinstance(object_id, str):
        return {'id': ObjectId(object_id)}
    elif isinstance(object_id, int):
        return {'int_id': object_id}
    else:
        raise ValueError(f'Unsupported id type: {object_id} {type(object_id)}')
