import datetime

from mongoengine import fields, connect


class ProductRegistrations(fields.EmbeddedDocument):
    full_name = fields.StringField()
    dance_role = fields.BaseField(choices=['leader', 'follower'])
    registration = fields.ReferenceField('RegistrationDocument')
    accepted = fields.BooleanField(default=False)


class EventProductDocument(fields.EmbeddedDocument):
    name = fields.StringField(required=True)
    key = fields.StringField(required=True)
    info = fields.MultiLineStringField()
    max_available = fields.IntField(min_value=0, default=0)
    base_price = fields.DecimalField(default=0)
    image_url = fields.URLField()

    product_class = fields.StringField(required=True)
    product_class_parameters = fields.DictField()
    tags = fields.ListField(fields.StringField())

    registrations = fields.EmbeddedDocumentListField(ProductRegistrations)


class EventDocument(fields.Document):
    __meta__ = {
        'collection': 'events',
        'indexes': ['name_key', 'start_date', 'active']
    }
    name = fields.StringField(required=True)
    key = fields.StringField(required=True)
    start_date = fields.DateTimeField(required=True)
    end_date = fields.DateTimeField(required=True)
    active = fields.BooleanField()
    products = fields.EmbeddedDocumentListField(EventProductDocument)


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

    def create_event(self, event):
        pass
