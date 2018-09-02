import datetime

import dataclasses
from mongoengine import fields, connect
from salty_tickets import models
from salty_tickets.constants import FOLLOWER, LEADER, REGISTRATION_STATUSES, NEW
from salty_tickets.models.event import Event
from salty_tickets.models.order import Order, Purchase, Payment, PurchaseItem
from salty_tickets.models.products import BaseProduct, ProductRegistration
from salty_tickets.mongo_utils import fields_from_dataclass


# @fields_from_dataclass(ProductRegistration, skip=['registration', 'as_couple', 'details'])
# class ProductRegistrationDocument(fields.EmbeddedDocument):
#     full_name = fields.StringField()
#     email = fields.EmailField()
#     dance_role = fields.BaseField(choices=[LEADER, FOLLOWER])
#     status = fields.BaseField(
#         choices=REGISTRATION_STATUSES,
#         default=NEW)
#     registration = fields.ReferenceField('RegistrationDocument')
#     partner_registration = fields.ReferenceField('RegistrationDocument', null=True)
#     #
#     # def to_model_short(self):
#     #     return mongo_to_dataclass(self, ProductRegistration, skip_fields=['registration'])
#
#     def to_dataclass(self):
#         model = self._to_dataclass()
#         if self.partner_registration:
#             model.as_couple = True
#             model.partner_name = self.partner_registration.full_name
#             model.partner_email = self.partner_registration.email
#         return model


@fields_from_dataclass(BaseProduct, skip=['registrations', 'product_class', 'product_class_parameters'])
class EventProductDocument(fields.EmbeddedDocument):
    image_url = fields.URLField()

    product_class = fields.StringField(required=True)
    product_class_parameters = fields.DictField()

    # registrations = fields.EmbeddedDocumentListField(ProductRegistrationDocument)

    @classmethod
    def from_dataclass(cls, model_dataclass):
        model_dict = dataclasses.asdict(model_dataclass)
        # registrations = model_dict.pop('registrations')
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
        # for registration in self.registrations:
        #     product_model.registrations.append(registration.to_dataclass())
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
        # product_docs = [p.to_dataclass() for p in self.products.values()]
        # if product_docs:
        #     event_model.append_products(product_docs)
        for p_key, prd in self.products.items():
            product_doc = prd.to_dataclass()
            for reg in RegistrationDocument.objects(event=self, products__product_key=p_key).all():
                reg_prod = [p for p in reg.products if p.product_key == p_key][0]
                reg_doc = ProductRegistration(
                    full_name=reg.full_name,
                    email=reg.email,
                    status=reg_prod.status,
                    dance_role=reg_prod.dance_role,
                )
                if reg_prod.partner_registration is not None:
                    reg_doc.as_couple = True
                    ptn_reg = reg_prod.partner_registration.fetch()
                    reg_doc.details['partner_name'] = ptn_reg.full_name
                    reg_doc.details['partner_email'] = ptn_reg.email
                product_doc.registrations.append(reg_doc)
            event_model.products[p_key] = product_doc

        return event_model


class RegistrationGroupDocument(fields.Document):
    __meta__ = {
        'collection': 'registration_groups'
    }
    type = fields.StringField()
    parameters = fields.DictField()


class RegistrationProductDetailsDocument(fields.EmbeddedDocument):
    product_key = fields.StringField(null=False)
    status = fields.StringField(choices=REGISTRATION_STATUSES, default=NEW)
    dance_role = fields.StringField(choices=[LEADER, FOLLOWER], null=True)
    partner_registration = fields.LazyReferenceField('RegistrationDocument', null=True)


class RegistrationDocument(fields.Document):
    __meta__ = {
        'collection': 'registrations'
    }
    full_name = fields.StringField(required=True)
    email = fields.EmailField(required=True)
    comment = fields.StringField()
    registered_datetime = fields.DateTimeField(null=False, default=datetime.datetime.utcnow)

    location = fields.DictField()

    event = fields.ReferenceField(EventDocument)
    products = fields.EmbeddedDocumentListField(RegistrationProductDetailsDocument)
    registration_groups = fields.ListField(fields.ReferenceField(RegistrationGroupDocument))


@fields_from_dataclass(PurchaseItem)
class PurchaseItemDocument(fields.EmbeddedDocument):
    pass


@fields_from_dataclass(Payment)
class PaymentDocument(fields.EmbeddedDocument):
    date = fields.DateTimeField(null=False, default=datetime.datetime.utcnow)


@fields_from_dataclass(Purchase, skip=['items'])
class PurchaseDocument(fields.EmbeddedDocument):
    items = fields.EmbeddedDocumentListField(PurchaseItemDocument)

    @classmethod
    def from_dataclass(cls, purchase_dataclass):
        purchase_doc = cls._from_dataclass(purchase_dataclass)
        purchase_doc.items = [PurchaseItemDocument.from_dataclass(i) for i in purchase_dataclass.items]

    def to_dataclass(self):
        purchase_dataclass = self._to_dataclass()
        purchase_dataclass.items = [i.to_dataclass() for i in self.items]


@fields_from_dataclass(Order, skip=['event', 'registrations', 'purchases', 'payments'])
class OrderDocument(fields.Document):
    __meta__ = {
        'collection': 'orders'
    }
    event = fields.ReferenceField(EventDocument)

    registrations = fields.ListField(fields.ReferenceField(RegistrationDocument))
    purchases = fields.EmbeddedDocumentListField(PurchaseDocument)
    payments = fields.EmbeddedDocumentListField(PaymentDocument)

    @classmethod
    def from_dataclass(cls, order_dataclass):
        order_doc = cls._from_dataclass(order_dataclass)
        order_doc.purchases = [PurchaseDocument.from_dataclass(p) for p in order_dataclass.purchases]
        order_doc.payments = [PaymentDocument.from_dataclass(p) for p in order_dataclass.payments]
        return order_doc

    def to_dataclass(self):
        order_model = self._to_dataclass()
        order_model.purchases = [p.to_dataclass() for p in self.purchases]
        order_model.payments = [p.to_dataclass() for p in self.payments]


class TicketsDAO:
    def __init__(self):
        connect(host='mongomock://localhost')

    def get_event_by_key(self, key):
        event_doc = EventDocument.objects(key=key).first()
        if event_doc is not None:
            return event_doc.to_dataclass()

    def create_event(self, event_model):
        event_doc = EventDocument.from_dataclass(event_model)
        event_doc.save()
