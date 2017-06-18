from datetime import datetime

from flask import url_for
from salty_tickets.models import Event, OrderProduct, Order, Registration, ORDER_PRODUCT_STATUS_WAITING
from salty_tickets.products import get_product_by_model
from salty_tickets.tokens import email_deserialize, order_product_serialize, order_product_deserialize


def price_format(func):
    def func_wrap(self):
        return '£{:.2f}'.format(func(self))
    return func_wrap


class OrderProductController:
    def __init__(self, order_product):
        self._order_product = order_product

    @classmethod
    def from_token(cls, order_product_token):
        order_product = order_product_deserialize(order_product_token)
        if order_product:
            return cls(order_product)

    @property
    def name(self):
        product = get_product_by_model(self._order_product.product)
        if hasattr(product, 'get_name'):
            return product.get_name(self._order_product)
        else:
            return self._order_product.product.name

    @property
    @price_format
    def price(self):
        return self._order_product.price

    @property
    def status(self):
        return self._order_product.status

    @property
    def is_waiting(self):
        return self.status == ORDER_PRODUCT_STATUS_WAITING

    @property
    def token(self):
        registration_datetime_diff = datetime.now() - self._order_product.order.order_datetime
        if self.is_waiting or registration_datetime_diff.total_seconds() < 60*60*24:
            return order_product_serialize(self._order_product)
        else:
            return ''

    @property
    def cancel_url(self):
        return url_for('event_order_product_cancel',
                       event_key=self._order_product.order.event.event_key,
                       order_product_token=self.token,
                       _external=True)


class OrderSummaryController:
    def __init__(self, order):
        self._order = order

    @property
    @price_format
    def transaction_fee(self):
        return self._order.transaction_fee

    @property
    @price_format
    def total_price(self):
        total_price = self._order.total_price + self._order.transaction_fee
        return total_price

    @property
    def show_order_summary(self):
        return len(self._order.order_products.all()) > 0

    @property
    def order_products(self):
        for order_product in self._order.order_products:
            yield OrderProductController(order_product)

    @property
    def has_waiting_list(self):
        for p in self.order_products:
            if p.is_waiting:
                return True
        return False


class EventOrderController:
    def __init__(self, event, email, order_products):
        self.email = email
        self._event = event
        self._order_products = order_products

    @classmethod
    def from_email_token(cls, event_key, email_token):
        email = email_deserialize(email_token)
        event = Event.query.filter_by(event_key=event_key).first()
        order_products = cls._get_order_products_for_email(event_key, email)
        return cls(event, email, order_products)

    @staticmethod
    def _get_order_products_for_email(event_key, email):
        order_products = OrderProduct.query. \
                            join(Order, aliased=True).join(Event, aliased=True).filter_by(event_key=event_key). \
                            join(Registration, aliased=True).filter_by(email=email). \
                            all()
        return order_products

    @property
    def order_products(self):
        for order_product in self._order_products:
            yield OrderProductController(order_product)
