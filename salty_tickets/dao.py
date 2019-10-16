import datetime
import typing
from typing import List

import dataclasses
from bson import ObjectId
import mongoengine as me
from salty_tickets import models
from salty_tickets.constants import FOLLOWER, LEADER, SUCCESSFUL
from salty_tickets.models.discounts import DiscountProduct, DiscountCode
from salty_tickets.models.email_campaigns import EventEmailSettings
from salty_tickets.models.event import Event
from salty_tickets.models.products import Product
from salty_tickets.models.registrations import Payment, Person, Registration, PaymentStripeDetails, Purchase, Discount, \
    RegistrationGroup, TransactionDetails
from salty_tickets.models.tickets import Ticket, RoleNumbers, TicketNumbers
from salty_tickets.utils.mongo_utils import fields_from_dataclass
from salty_tickets.utils.utils import timeit


@fields_from_dataclass(Registration, skip=['person', 'partner', 'registered_by', 'as_couple', 'details'])
class RegistrationDocument(me.Document):
    meta = {
        'collection': 'registrations'
    }
    dance_role = me.fields.BaseField(choices=[LEADER, FOLLOWER], null=True)
    person = me.ReferenceField('PersonDocument', required=True)
    partner = me.ReferenceField('PersonDocument', null=True)
    registered_by = me.ReferenceField('PersonDocument', required=True)
    ticket_key = me.StringField(required=True)
    event = me.ReferenceField('EventDocument', required=True)

    def to_dataclass(self):
        model = self._to_dataclass()
        model.person = self.person.to_dataclass()
        model.registered_by = self.registered_by.to_dataclass()
        if self.partner:
            model.partner = self.partner.to_dataclass()

        # migration
        if not self.is_paid and self.price == self.paid_price:
            self.is_paid = True
            self.save()
            model.is_paid = True

        return model


@fields_from_dataclass(Purchase, skip=['person'])
class PurchaseDocument(me.Document):
    meta = {
        'collection': 'purchases',
    }
    person = me.ReferenceField('PersonDocument', required=True)
    event = me.ReferenceField('EventDocument', required=True)

    def to_dataclass(self):
        model = self._to_dataclass()
        model.person = self.person.to_dataclass()

        # migration
        if not self.is_paid and self.price == self.paid_price:
            self.is_paid = True
            self.save()
            model.is_paid = True

        return model


@fields_from_dataclass(Discount, skip=['person'])
class DiscountDocument(me.EmbeddedDocument):
    person = me.ReferenceField('PersonDocument', required=True)

    def to_dataclass(self):
        model = self._to_dataclass()
        model.person = self.person.to_dataclass()
        return model

    @classmethod
    def from_dataclass(cls, model: Discount):
        doc = cls._from_dataclass(model)
        doc.person = model.person.id
        return doc


@fields_from_dataclass(Ticket, skip=['registrations', 'ticket_class', 'ticket_class_parameters', 'numbers'])
class TicketDocument(me.EmbeddedDocument):
    image_url = me.URLField()

    ticket_class = me.StringField(required=True)
    ticket_class_parameters = me.DictField()

    @classmethod
    def from_dataclass(cls, model_dataclass):
        model_dict = dataclasses.asdict(model_dataclass)
        base_fields = [f.name for f in dataclasses.fields(Ticket)]
        kwargs = {f: model_dict.pop(f) for f in base_fields if f in model_dict}
        # kwargs.pop('registrations')
        kwargs.pop('numbers')
        kwargs['ticket_class'] = model_dataclass.__class__.__name__
        kwargs['ticket_class_parameters'] = model_dict
        ticket_doc = cls(**kwargs)
        return ticket_doc

    def to_dataclass(self):
        kwargs = self.ticket_class_parameters
        model_class = getattr(models.tickets, self.ticket_class)
        model_fields = [f.name for f in dataclasses.fields(Ticket) if f.name not in ['registrations', 'numbers']]
        kwargs.update({f: getattr(self, f) for f in model_fields})
        ticket_model = model_class(**kwargs)
        return ticket_model


@fields_from_dataclass(Product)
class ProductDocument(me.EmbeddedDocument):
    pass


@fields_from_dataclass(DiscountProduct, skip=['discount_product_class', 'discount_product_parameters'])
class DiscountProductDocument(me.EmbeddedDocument):
    discount_product_class = me.StringField(required=True)
    discount_product_parameters = me.DictField()

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


@fields_from_dataclass(RoleNumbers)
class RoleNumbersDocument(me.EmbeddedDocument):
    accepted = me.IntField(required=True)
    waiting = me.IntField(required=False)
    is_wait_listed = me.BooleanField()
    waiting_probability = me.IntField(required=False)


@fields_from_dataclass(TicketNumbers, skip=['roles'])
class TicketNumbersDocument(me.EmbeddedDocument):
    accepted = me.IntField(required=True)
    remaining = me.IntField()
    roles = me.MapField(me.EmbeddedDocumentField(RoleNumbersDocument))

    @classmethod
    def from_dataclass(cls, model_dataclass: TicketNumbers):
        doc = cls._from_dataclass(model_dataclass)
        doc.roles = {k: RoleNumbersDocument.from_dataclass(v)
                     for k, v in model_dataclass.roles.items()}
        return doc

    def to_dataclass(self) -> TicketNumbers:
        model_dataclass = self._to_dataclass()
        model_dataclass.roles = {k: v.to_dataclass() for k, v in self.roles.items()}
        return model_dataclass


class EventTicketsNumbersDocument(me.Document):
    meta = {
        'collection': 'event_ticket_numbers',
    }
    event_key = me.StringField(primary_key=True)
    ticket_numbers = me.MapField(me.EmbeddedDocumentField(TicketNumbersDocument))


@fields_from_dataclass(Event, skip=['tickets', 'merchandise', 'discount_products', 'ticket_numbers'])
class EventDocument(me.Document):
    meta = {
        'collection': 'events',
        'strict': False
    }
    key = me.StringField()
    tickets = me.MapField(me.EmbeddedDocumentField(TicketDocument))
    products = me.MapField(me.EmbeddedDocumentField(ProductDocument))
    discount_products = me.MapField(me.EmbeddedDocumentField(DiscountProductDocument))
    ticket_numbers = me.ReferenceField(EventTicketsNumbersDocument, required=False)

    @classmethod
    def from_dataclass(cls, model_dataclass: Event):
        event_doc = cls._from_dataclass(model_dataclass)
        event_doc.tickets = {p_key: TicketDocument.from_dataclass(p)
                             for p_key, p in model_dataclass.tickets.items()}
        event_doc.products = {p_key: ProductDocument.from_dataclass(p)
                              for p_key, p in model_dataclass.products.items()}
        event_doc.discount_products = {p_key: DiscountProductDocument.from_dataclass(p)
                              for p_key, p in model_dataclass.discount_products.items()}
        return event_doc

    def to_dataclass(self) -> Event:
        event_model = self._to_dataclass()

        if self.ticket_numbers:
            ticket_numbers = {k: v.to_dataclass() for k, v in self.ticket_numbers.ticket_numbers.items()}
        else:
            ticket_numbers = {}

        for p_key, prd in self.tickets.items():
            ticket = prd.to_dataclass()
            ticket.numbers = ticket_numbers.get(ticket.key)
            event_model.tickets[p_key] = ticket

        for p_key, prd in self.products.items():
            product_doc = prd.to_dataclass()
            event_model.products[p_key] = product_doc

        for p_key, prd in self.discount_products.items():
            discount_product_doc = prd.to_dataclass()
            event_model.discount_products[p_key] = discount_product_doc

        return event_model


@fields_from_dataclass(RegistrationGroup, skip=['admin', 'members', 'event'])
class RegistrationGroupDocument(me.Document):
    __meta__ = {
        'collection': 'registration_groups'
    }
    int_id = me.SequenceField()
    event = me.ReferenceField(EventDocument)
    admin = me.ReferenceField('PersonDocument')
    members = me.ListField(me.ReferenceField('PersonDocument'))

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
class PersonDocument(me.Document):
    meta = {
        'collection': 'person_registrations',
    }
    event = me.ReferenceField(EventDocument)
    int_id = me.SequenceField()

    def to_dataclass(self):
        model = self._to_dataclass()
        model.int_id = self.int_id
        return model


@fields_from_dataclass(PaymentStripeDetails)
class PaymentStripeDetailsDocument(me.EmbeddedDocument):
    pass


@fields_from_dataclass(TransactionDetails)
class TransactionDocument(me.EmbeddedDocument):
    pass


@fields_from_dataclass(Payment, skip=['paid_by', 'event', 'registrations', 'purchases', 'discounts',
                                      'extra_registrations', 'transactions'])
class PaymentDocument(me.Document):
    meta = {
        'collection': 'payments'
    }
    date = me.DateTimeField(null=False, default=datetime.datetime.utcnow)
    paid_by = me.ReferenceField(PersonDocument)
    event = me.ReferenceField(EventDocument)
    registrations = me.ListField(me.ReferenceField(RegistrationDocument))
    extra_registrations = me.ListField(me.ReferenceField(RegistrationDocument))
    purchases = me.ListField(me.ReferenceField(PurchaseDocument))
    discounts = me.EmbeddedDocumentListField(DiscountDocument)
    stripe = me.EmbeddedDocumentField(PaymentStripeDetailsDocument)
    # int_id = fields.SequenceField()
    transactions = me.EmbeddedDocumentListField(TransactionDocument, null=True)

    def to_dataclass(self) -> Payment:
        model = self._to_dataclass(paid_by=self.paid_by.to_dataclass())
        model.registrations = [r.to_dataclass() for r in self.registrations]
        model.extra_registrations = [r.to_dataclass() for r in self.extra_registrations]
        model.purchases = [p.to_dataclass() for p in self.purchases]
        model.discounts = [p.to_dataclass() for p in self.discounts]
        if self.stripe:
            model.stripe = self.stripe.to_dataclass()
        # model.int_id = self.int_id

        model.transactions = [t.to_dataclass() for t in self.transactions or []]

        return model

    @classmethod
    def from_dataclass(cls, model):
        doc = cls._from_dataclass(model)
        if doc.stripe is not None:
            doc.stripe = PaymentStripeDetailsDocument.from_dataclass(model.stripe)
        return doc


@fields_from_dataclass(DiscountCode)
class DiscountCodeDocument(me.Document):
    meta = {
        'collection': 'discount_codes',
    }
    event = me.ReferenceField(EventDocument)
    int_id = me.SequenceField()

    def to_dataclass(self):
        model = self._to_dataclass()
        model.int_id = self.int_id
        return model


@fields_from_dataclass(EventEmailSettings)
class EventEmailSettingsDocument(me.Document):
    meta = {
        'collection': 'event_email_settings',
    }


class TicketsDAO:
    def __init__(self, host=None):
        if host is None:
            host = 'mongomock://localhost'

        me.connect(host=host)
        # from salty_tickets.utils.demo_db import salty_recipes
        # salty_recipes(self)

    def get_event_by_key(self, event_key, get_registrations=True) -> typing.Optional[Event]:
        event_doc = self._get_event_doc(event_key)
        if event_doc is None:
            return None

        event = event_doc.to_dataclass()
        # if get_registrations:
        #     registrations = self.query_registrations(event)
        #     for ticket_key in event.tickets:
        #         event.tickets[ticket_key].registrations = [r for r in registrations if r.ticket_key == ticket_key]

        return event

    def get_ticket_registrations(self, event: Event, tickets=None):
        registrations = self.query_registrations(event)
        ticket_registrations = {}
        for ticket_key in event.tickets:
            if tickets and ticket_key not in tickets:
                continue
            ticket_registrations[ticket_key] = [r for r in registrations if r.ticket_key == ticket_key]
        return ticket_registrations

    def get_registrations_for_ticket(self, event: Event, ticket) -> List[Registration]:
        filters = {
            'ticket_key': self._get_ticket_key(ticket),
            'event': event.id,
        }
        items = RegistrationDocument.objects(**filters).select_related(3)
        return [r.to_dataclass() for r in items]

    def get_event_ticket_numbers(self, event_key: str) -> typing.Dict[str, TicketNumbers]:
        doc = EventTicketsNumbersDocument.objects(id=event_key).first()
        if not doc:
            doc = EventTicketsNumbersDocument()
        return {k: v.to_dataclass() for k, v in doc.ticket_numbers.items()}

    def save_event_ticket_numbers(self, event_key: str, ticket_numbers: typing.Dict[str, TicketNumbers]):
        doc = EventTicketsNumbersDocument.objects(event_key=event_key).first()
        if not doc:
            doc = EventTicketsNumbersDocument(event_key=event_key)
        doc.ticket_numbers = {k: TicketNumbersDocument.from_dataclass(v)
                              for k, v in ticket_numbers.items()}
        doc.save()

        event_doc = self._get_event_doc(event_key)
        if event_doc.ticket_numbers != doc:
            event_doc.ticket_numbers = doc
            event_doc.save()

    def create_event(self, event_model):
        event_doc = EventDocument.from_dataclass(event_model)
        event_doc.save()
        event_model.id = event_doc.id

    def _get_event_doc(self, event) -> EventDocument:
        if isinstance(event, str):
            return EventDocument.objects(key=event).first()
        elif event.id:
            return EventDocument.objects(id=event.id).first()
        else:
            raise ValueError(f'Invalid event argument: {event}')

    def _get_event_id(self, event) -> EventDocument:
        if isinstance(event, str):
            return EventDocument.objects(key=event).first().id
        elif event.id:
            return event.id
        else:
            raise ValueError(f'Invalid event argument: {event}')

    def _get_ticket_key(self, ticket) -> str:
        if isinstance(ticket, str):
            return ticket
        else:
            return ticket.key

    def _get_or_create_new_person(self, person, event) -> PersonDocument:
        if not person.id:
            self.add_person(person, event)
        return PersonDocument.objects(id=person.id).first()

    def add_person(self, person: Person, event: Event):
        if person.id:
            raise ValueError(f'Person already exists: {person}')
        else:
            person_doc = PersonDocument.from_dataclass(person)
            person_doc.event = event.id
            person_doc.save()
            person.id = person_doc.id

    def add_registration(self, registration: Registration, event: Event):
        if registration.id:
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
        if purchase.id:
            raise ValueError(f'Purchase already exists: {purchase}')

        purchase_doc = PurchaseDocument.from_dataclass(purchase)
        purchase_doc.event = event.id
        purchase_doc.person = self._get_or_create_new_person(purchase.person, event)
        purchase_doc.save()
        purchase.id = purchase_doc.id

    @timeit
    def add_payment(self, payment: Payment, event: Event, register=False):
        if payment.id:
            raise ValueError(f'Payment already exists: {payment}')
        print(payment)
        payment_doc = PaymentDocument.from_dataclass(payment)
        payment_doc.event = event.id
        payment_doc.paid_by = self._get_or_create_new_person(payment.paid_by, event)
        for reg in payment.registrations:
            if not reg.id:
                if not register:
                    raise ValueError(f'Registrations need to be added first: {reg}')
                else:
                    self.add_registration(reg, event)
            payment_doc.registrations.append(reg.id)

        payment_doc.extra_registrations = [r.id for r in payment.extra_registrations]

        for prd in payment.purchases:
            if not prd.id:
                if not register:
                    raise ValueError(f'Purchases need to be added first: {reg}')
                else:
                    self.add_purchase(prd, event)
            payment_doc.purchases.append(prd.id)

        for discount in payment.discounts:
            payment_doc.discounts.append(DiscountDocument.from_dataclass(discount))

        for transaction in payment.transactions:
            payment_doc.transactions.append(TransactionDocument.from_dataclass(transaction))

        # payment_doc.discounts = [DiscountDocument.from_dataclass(d) for d in payment.discounts]

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

    def get_payment_by_registration(self, registration) -> Payment:
        if registration.id:
            payment_doc = PaymentDocument.objects.filter(registrations__contains=registration.id).first()
            if payment_doc:
                return payment_doc.to_dataclass()

    def query_registrations(self, event: Event, person: Person=None, registered_by: Person=None,
                            partner: Person=None, ticket=None) -> List[Registration]:
        filters = {'event': self._get_event_id(event)}
        if person is not None:
            filters['person'] = self._get_doc(PersonDocument, person)
        if registered_by is not None:
            filters['registered_by'] = self._get_doc(PersonDocument, registered_by)
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

    def update_purchase(self, purchase: Purchase):
        purchase_0 = self.get_purchase_by_id(purchase.id)
        extra_updates = {}
        event = PurchaseDocument.objects(id=purchase.id).first().event.key
        if purchase.person != purchase_0.person:
            extra_updates['person'] = self._get_or_create_new_person(purchase.person, event)

        self._update_doc(PurchaseDocument, purchase, **extra_updates)

    @timeit
    def update_payment(self, payment: Payment):
        self._update_doc(PaymentDocument, payment)

        doc = PaymentDocument.objects(**id_filter(payment.id)).first()
        transactions = [t.to_dataclass() for t in doc.transactions or []]
        if payment.transactions != transactions:
            doc.transactions = [TransactionDocument.from_dataclass(t) for t in payment.transactions or []]
            doc.save()
        if payment.discounts != [d.to_dataclass() for d in doc.discounts or []]:
            doc.discounts = [DiscountDocument.from_dataclass(d) for d in payment.discounts or []]
            doc.save()

    def mark_registrations_as_couple(self, registration_1: Registration, registration_2: Registration) -> Payment:
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

    def get_purchase_by_id(self, object_id) -> Purchase:
        doc = PurchaseDocument.objects(**id_filter(object_id)).first()
        if doc:
            return doc.to_dataclass()

    def get_discount_code_by_id(self, object_id) -> Person:
        doc = DiscountCodeDocument.objects(**id_filter(object_id)).first()
        if doc:
            return doc.to_dataclass()

    def add_discount_code(self, event: Event, discount_code: DiscountCode):
        if discount_code.id:
            raise ValueError(f'Discount code already exists: {discount_code}')
        discount_code_doc = DiscountCodeDocument.from_dataclass(discount_code)
        discount_code_doc.event = event.id
        discount_code_doc.save()
        discount_code.id = discount_code_doc.id
        discount_code.int_id = discount_code_doc.int_id

    def increment_discount_code_usages(self, discount_code: DiscountCode, usages=1):
        if not discount_code.id:
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
        if not person.id:
            raise ValueError('Person need to be saved first')
        if not registration_group.id:
            raise ValueError('Registration group need to be saved first')

        doc = RegistrationGroupDocument.objects(**id_filter(registration_group.id)).first()
        doc.members.append(person.id)
        doc.save()
        registration_group.members.append(person)

    def new_event_email_settings(self, event_email_settings: EventEmailSettings):
        doc = self.get_event_email_settings(event_email_settings.event_key)
        if doc is not None:
            raise ValueError('Email settings already exist for event')
        doc = EventEmailSettingsDocument.from_dataclass(event_email_settings)
        doc.save()
        event_email_settings.id = doc.id

    def get_event_email_settings(self, event_key) -> EventEmailSettings:
        doc = EventEmailSettingsDocument.objects(event_key=event_key).first()
        if doc is not None:
            return doc.to_dataclass()

    def update_event_email_settings(self, event_email_settings: EventEmailSettings):
        self._update_doc(EventEmailSettingsDocument, event_email_settings)

    def get_person_event_key(self, person: Person) -> str:
        if not person.id:
            return None
        person_doc = PersonDocument.objects(**id_filter(person.id)).first()
        if person_doc:
            return person_doc.event.key


def id_filter(object_id):
    if isinstance(object_id, ObjectId):
        return {'id': object_id}
    elif isinstance(object_id, str):
        return {'id': ObjectId(object_id)}
    elif isinstance(object_id, int):
        return {'int_id': object_id}
    else:
        raise ValueError(f'Unsupported id type: {object_id} {type(object_id)}')
