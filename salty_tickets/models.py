from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Boolean, func
from sqlalchemy.orm import relationship
from sqlalchemy_utils import aggregated
from .database import Base
from .utils import string_to_key
import datetime
__author__ = 'vnkrv'


class Event(Base):
    __tablename__ = 'events'
    id = Column(Integer, primary_key=True)
    event_key = Column(String(50), unique=False, nullable=False)
    name = Column(String(50), nullable=False)
    info = Column(String)
    event_type = Column(String(25))
    start_date = Column(DateTime, nullable=False)
    active = Column(Boolean, nullable=False, default=True)

    products = relationship('Product', lazy='dynamic')
    registrations = relationship('Registration', lazy='dynamic')

    def __init__(self, name, start_date, **kwargs):
        self.name = name
        self.start_date = start_date
        self.event_key = string_to_key(self.name)
        super(Event, self).__init__(**kwargs)


class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('events.id'))
    name = Column(String(50))
    type = Column(String(50), nullable=False)
    info = Column(String)
    price = Column(Float, default=0)
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


class ProductParameter(Base):
    __tablename__ = 'product_parameters'
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    parameter_name = Column(String(50))
    parameter_value = Column(String(50))

    def __init__(self, name, value, **kwargs):
        self.parameter_name = name
        self.parameter_value = value
        super(ProductParameter, self).__init__(**kwargs)


class Registration(Base):
    __tablename__ = 'registrations'
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('events.id'))
    name = Column(String(50), nullable=False)
    email = Column(String(120), nullable=False)
    registered_datetime = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    orders = relationship("Order", lazy='dynamic')

    def __repr__(self):
        return '<User %r>' % self.name


class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    registration_id = Column(Integer, ForeignKey('registrations.id'))
    total_price = Column(Float, nullable=False, default=0)
    transaction_fee = Column(Float, nullable=False, default=0)
    status = Column(String, nullable=False)
    order_datetime = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    # @aggregated('order_products', Column(Float))
    @property
    def products_price(self):
        # return func.sum(OrderProduct.price)
        return sum([p.price for p in self.order_products.all()])

    registration = relationship('Registration', uselist=False)
    order_products = relationship('OrderProduct', lazy='dynamic')


class OrderProduct(Base):
    __tablename__ = 'order_products'
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    registration_id = Column(Integer, ForeignKey('registrations.id'))
    price = Column(Float, nullable=False)
    details = relationship("OrderProductDetail", lazy='dynamic')
    order = relationship('Order', uselist=False)
    product = relationship('Product', uselist=False)

    def __init__(self, product, price, details_dict=None, **kwargs):
        self.product = product
        self.price = price
        if details_dict:
            for key, value in details_dict.items():
                self.details.append(OrderProductDetail(key, value))
        super(OrderProduct, self).__init__(**kwargs)


class OrderProductDetail(Base):
    __tablename__ = 'order_product_details'
    id = Column(Integer, primary_key=True)
    order_product_id = Column(Integer, ForeignKey('order_products.id'))
    field_name = Column(String(50), nullable=False)
    field_value = Column(String(50), nullable=False)

    def __init__(self, field_name, field_value, **kwargs):
        self.field_name = field_name,
        self.field_value = field_value
        super(OrderProductDetail, self).__init__(**kwargs)


class OrderProductRegistrationsMapping:
    __tablename__ = 'order_product_registrations_mapping'
    id = Column(Integer, primary_key=True)
    order_product_id = Column(Integer, ForeignKey('order_products.id'))
    registration_id = Column(Integer, ForeignKey('registrations.id'))

