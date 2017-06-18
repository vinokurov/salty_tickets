from collections import namedtuple

from salty_tickets.models import Event, OrderProduct, Order, Registration, ORDER_PRODUCT_STATUS_WAITING
from salty_tickets.products import get_product_by_model
from salty_tickets.tokens import token_to_email


OrderProductInfo = namedtuple('OrderProductInfo', ['name', 'price', 'status'])

def get_order_product_info(order_product_query):
    products = []
    for order_product in order_product_query.all():
        price = order_product.price
        product = get_product_by_model(order_product.product)
        if hasattr(product, 'get_name'):
            name = product.get_name(order_product)
        else:
            name = order_product.product.name
        products.append(OrderProductInfo(name=name, price=price, status=order_product.status))
        print(OrderProductInfo(name=name, price=price, status=order_product.status))
    return products


class OrderSummaryController:
    def __init__(self, order, order_product_info_list):
        self.order = order
        self.order_product_info_list = order_product_info_list

    @property
    def transaction_fee(self):
        return self.price_format(self.order.transaction_fee)

    @property
    def total_price(self):
        total_price = self.order.total_price + self.order.transaction_fee
        return self.price_format(total_price)

    @property
    def show_order_summary(self):
        return len(self.order_product_info_list) > 0

    @classmethod
    def from_order(cls, order):
        assert isinstance(order, Order)
        order_product_info_list = get_order_product_info(order.order_products)
        return cls(order, order_product_info_list)

    @staticmethod
    def price_format(price):
        return '{:.2f}'.format(price)


    @staticmethod
    def is_waiting_list(order_product_info):
        return order_product_info.status == ORDER_PRODUCT_STATUS_WAITING


class EventOrderController:
    def __init__(self, event_key, email, order_product_info_list):
        self.email = email
        self.event_key = event_key
        self.order_product_info_list = order_product_info_list

    @classmethod
    def from_email_token(cls, event_key, email_token):
        email = token_to_email(email_token)
        order_product_info_list = cls._get_order_product_info_list(event_key, email)
        return cls(event_key, email, order_product_info_list)

    @staticmethod
    def _get_order_product_info_list(event_key, email):
        order_products_query = OrderProduct.query. \
                                join(Order, aliased=True).join(Event, aliased=True).filter_by(event_key=event_key). \
                                join(Registration, aliased=True).filter_by(email=email). \
                                all()
        order_product_info_list = get_order_product_info(order_products_query)
        return order_product_info_list
