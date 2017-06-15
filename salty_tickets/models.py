import datetime

from flask import jsonify
from salty_tickets import config
from salty_tickets.database import Base
# from salty_tickets.products import get_product_by_model
from salty_tickets.utils import string_to_key
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Boolean
from sqlalchemy import Table
from sqlalchemy import Text
from sqlalchemy.orm import relationship

__author__ = 'vnkrv'


ORDER_STATUS_NEW = 'new'
ORDER_STATUS_PAID = 'paid'
ORDER_STATUS_FAILED = 'failed'

DANCE_ROLE_LEADER = 'leader'
DANCE_ROLE_FOLLOWER = 'follower'

ORDER_PRODUCT_STATUS_WAITING = 'waiting'
ORDER_PRODUCT_STATUS_ACCEPTED = 'accepted'
ORDER_PRODUCT_STATUS_CANCELLED = 'cancelled'

SIGNUP_GROUP_TYPE_PARTNERS = 'partners'


class Event(Base):
    __tablename__ = 'events'
    id = Column(Integer, primary_key=True)
    event_key = Column(String(255), unique=False, nullable=False)
    name = Column(String(255), nullable=False)
    info = Column(Text)
    event_type = Column(String(25))
    start_date = Column(DateTime, nullable=False)
    active = Column(Boolean, nullable=False, default=True)

    products = relationship('Product', lazy='dynamic')
    orders = relationship('Order', lazy='dynamic')

    def __init__(self, name, start_date, **kwargs):
        self.name = name
        self.start_date = start_date
        self.event_key = string_to_key(self.name)
        super(Event, self).__init__(**kwargs)


class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('events.id'))
    name = Column(String(255))
    type = Column(String(50), nullable=False)
    info = Column(Text)
    price = Column(Float, default=0, )
    max_available = Column(Integer, default=0)
    image_url = Column(String(255))
    parameters = relationship('ProductParameter', lazy='dynamic')

    def __init__(self, name, product_type, parameters_dict=None, **kwargs):
        self.name = name
        self.type = product_type
        if parameters_dict:
            self.add_parameters(parameters_dict)
        super(Product, self).__init__(**kwargs)

    def add_parameters(self, parameters_dict):
        for k, v in parameters_dict.items():
            self.parameters.append(ProductParameter(k, v))

    @property
    def product_key(self):
        return string_to_key(self.name)

    @property
    def parameters_as_dict(self):
        details_dict = {d.parameter_name: d.parameter_value for d in self.parameters.all()}
        return details_dict


class ProductParameter(Base):
    __tablename__ = 'product_parameters'
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    parameter_name = Column(String(255))
    parameter_value = Column(String(255))

    def __init__(self, name, value, **kwargs):
        self.parameter_name = name
        self.parameter_value = value
        super(ProductParameter, self).__init__(**kwargs)


class Registration(Base):
    __tablename__ = 'registrations'
    id = Column(Integer, primary_key=True)
    # event_id = Column(Integer, ForeignKey('events.id'))
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    comment = Column(Text)
    registered_datetime = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    # orders = relationship("Order", lazy='dynamic')
    # event = relationship("Event", uselist=False)
    crowdfunding_registration_properties = relationship('CrowdfundingRegistrationProperties', uselist=False)
    order = relationship('Order', uselist=False)

    def __repr__(self):
        return '<User %r>' % self.name


class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    registration_id = Column(Integer, ForeignKey('registrations.id'))
    event_id = Column(Integer, ForeignKey('events.id'))
    total_price = Column(Float, nullable=False, default=0)
    transaction_fee = Column(Float, nullable=False, default=0)
    status = Column(String(50), nullable=False, default=ORDER_STATUS_NEW)
    order_datetime = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    stripe_charge_id = Column(String(50))
    # stripe_charge = Column(Text)

    registration = relationship('Registration', uselist=False)
    event = relationship("Event", uselist=False)
    order_products = relationship('OrderProduct', lazy='dynamic')

    # @aggregated('order_products', Column(Float))
    @property
    def products_price(self):
        # return self.order_products.with_entities(func.sum(OrderProduct.price)).scalar()
        return sum([p.price for p in self.order_products.all()])

    @property
    def stripe_amount(self):
        return int((self.total_price + self.transaction_fee) * 100)

    def charge(self, stripe_token):
        import stripe
        stripe.api_key = config.STRIPE_SK

        try:
            charge = stripe.Charge.create(
                amount=self.stripe_amount,
                currency='gbp',
                description=self.event.name,
                metadata=dict(order_id=self.id),
                source=stripe_token
            )
            print(charge)
            self.stripe_charge_id = charge['id']
            # self.stripe_charge = jsonify(charge)
            self.status = ORDER_STATUS_PAID
            return True, charge
        except stripe.CardError as ce:
            self.stripe_charge_id = charge.get('id', '')
            self.stripe_charge = jsonify(ce)
            # self.status = ORDER_STATUS_FAILED
            return False, ce


class OrderProduct(Base):
    __tablename__ = 'order_products'
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    price = Column(Float, nullable=False)

    details = relationship("OrderProductDetail", lazy='dynamic')
    order = relationship('Order', uselist=False)
    product = relationship('Product', uselist=False)

    registrations = relationship('Registration', secondary='order_product_registrations_mapping')

    def __init__(self, product, price, details_dict=None, **kwargs):
        self.product = product
        self.price = price
        if details_dict:
            for key, value in details_dict.items():
                self.details.append(OrderProductDetail(key, value))
        super(OrderProduct, self).__init__(**kwargs)

    @property
    def details_as_dict(self):
        details_dict = {d.field_name: d.field_value for d in self.details.all()}
        return details_dict

    def cancel(self):
        raise NotImplementedError

    def refund(self, amount):
        raise NotImplementedError

    def accept(self):
        status = self.details.query.filter_by(field_name='status').one()
        status.field_value = ORDER_PRODUCT_STATUS_ACCEPTED


class OrderProductDetail(Base):
    __tablename__ = 'order_product_details'
    id = Column(Integer, primary_key=True)
    order_product_id = Column(Integer, ForeignKey('order_products.id'))
    field_name = Column(String(255), nullable=False)
    field_value = Column(String(255), nullable=False)

    def __init__(self, field_name, field_value, **kwargs):
        self.field_name = field_name
        self.field_value = field_value
        super(OrderProductDetail, self).__init__(**kwargs)

order_product_registrations_mapping = Table('order_product_registrations_mapping', Base.metadata,
    Column('order_product_id', Integer, ForeignKey('order_products.id')),
    Column('registration_id', Integer, ForeignKey('registrations.id'))
    )


class CrowdfundingRegistrationProperties(Base):
    __tablename__ = 'crowdfunding_registration_properties'
    id = Column(Integer, primary_key=True)
    registration_id = Column(Integer, ForeignKey('registrations.id'))
    anonymous = Column(Boolean, nullable=False, default=False)


# class RegistrationPartners(Base):
#     __tablename__ = 'registration_partners'
#     id = Column(Integer, primary_key=True)
#     order_product_id1 = Column(Integer, ForeignKey('order_products.id'))
#     order_product_id2 = Column(Integer, ForeignKey('order_products.id'))

    # order_product1 = relationship()

class SignupGroup(Base):
    __tablename__ = 'signup_groups'
    id = Column(Integer, primary_key=True)
    type = Column(String(32))
    event_id = Column(Integer, ForeignKey('events.id'))

group_order_product_mapping = Table('group_order_product_mapping', Base.metadata,
    Column('order_product_id', Integer, ForeignKey('order_products.id')),
    Column('signup_group_id', Integer, ForeignKey('signup_groups.id'))
    )

