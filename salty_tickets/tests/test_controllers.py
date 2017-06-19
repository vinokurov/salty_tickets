from datetime import datetime, timedelta

import pytest
from salty_tickets.controllers import OrderSummaryController, OrderProductController, price_format
from salty_tickets.models import ORDER_PRODUCT_STATUS_WAITING, ORDER_PRODUCT_STATUS_ACCEPTED, Order, OrderProduct, \
    Product
from mock import Mock
from salty_tickets.tokens import order_product_serialize


def test_OrderProductController_price():
    order_product = Mock(spec=OrderProduct)
    order_product.price = 10.123
    controller = OrderProductController(order_product)
    assert controller.price == '£10.12'


def test_OrderProductController_status():
    order_product = Mock(spec=OrderProduct)
    order_product.status = ORDER_PRODUCT_STATUS_WAITING
    controller = OrderProductController(order_product)
    assert controller.status == ORDER_PRODUCT_STATUS_WAITING


def test_OrderProductController_is_waiting():
    order_product = Mock(spec=OrderProduct)
    order_product.status = ORDER_PRODUCT_STATUS_WAITING
    controller = OrderProductController(order_product)
    assert controller.is_waiting == True

    order_product = Mock(spec=OrderProduct)
    order_product.status = ORDER_PRODUCT_STATUS_ACCEPTED
    controller = OrderProductController(order_product)
    assert controller.is_waiting == False


def test_OrderProductController_token():
    order_product = Mock(spec=OrderProduct)
    order_product.id = 123
    token = order_product_serialize(order_product)

    # waiting list => return token
    order_product.status = ORDER_PRODUCT_STATUS_WAITING
    order_product.order = Mock(order_datetime=datetime(2015, 1, 1, 17, 0))
    controller = OrderProductController(order_product)
    assert controller.token == token

    # registered less than a day ago => return token
    order_product.status = ORDER_PRODUCT_STATUS_ACCEPTED
    order_product.order = Mock(order_datetime=datetime.now() - timedelta(hours=23))
    controller = OrderProductController(order_product)
    assert controller.token == token

    # registered more than a day ago => no token
    order_product.status = ORDER_PRODUCT_STATUS_ACCEPTED
    order_product.order = Mock(order_datetime=datetime.now() - timedelta(hours=25))
    controller = OrderProductController(order_product)
    assert controller.token == ''


def test_decorator_price_format():
    @price_format
    def get_price(price_float):
        return price_float

    assert get_price(10) == '£10.00'
    assert get_price(10.123) == '£10.12'
    assert get_price(10.229) == '£10.23'


def test_OrderSummaryController_transaction_fee():
    order = Order(total_price=100, transaction_fee=1.5)
    order_controller = OrderSummaryController(order=order)
    assert order_controller.transaction_fee == '£1.50'


def test_OrderSummaryController_total_price():
    order = Order(total_price=100, transaction_fee=1.5)
    order_controller = OrderSummaryController(order=order)
    assert order_controller.total_price == '£101.50'


def test_OrderSummaryController_show_order_summary():
    order = Order(total_price=100, transaction_fee=1.5)
    order_controller = OrderSummaryController(order=order)
    assert order_controller.show_order_summary == False

    product = Product('Test', 'Test')
    order.order_products.append(OrderProduct(product, 10))
    order_controller = OrderSummaryController(order=order)
    assert order_controller.show_order_summary == True
