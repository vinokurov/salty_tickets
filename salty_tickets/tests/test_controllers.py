import pytest
from salty_tickets.controllers import OrderProductInfo, OrderSummaryController
from salty_tickets.models import ORDER_PRODUCT_STATUS_WAITING, ORDER_PRODUCT_STATUS_ACCEPTED, Order


def test_OrderSummaryController_is_waiting_list():
    product_info = OrderProductInfo(name='test', price=100, status=ORDER_PRODUCT_STATUS_WAITING)
    assert OrderSummaryController.is_waiting_list(product_info) == True

    product_info = OrderProductInfo(name='test', price=100, status=ORDER_PRODUCT_STATUS_ACCEPTED)
    assert OrderSummaryController.is_waiting_list(product_info) == False


def test_OrderSummaryController_price_format():
    assert OrderSummaryController.price_format(10) == '10.00'
    assert OrderSummaryController.price_format(10.123) == '10.12'
    assert OrderSummaryController.price_format(10.229) == '10.23'


def test_OrderSummaryController_transaction_fee():
    order = Order(total_price=100, transaction_fee=1.5)
    order_controller = OrderSummaryController(order=order, order_product_info_list=[])
    assert order_controller.transaction_fee == '1.50'


def test_OrderSummaryController_total_price():
    order = Order(total_price=100, transaction_fee=1.5)
    order_controller = OrderSummaryController(order=order, order_product_info_list=[])
    assert order_controller.total_price == '101.50'


def test_OrderSummaryController_show_order_summary():
    order = Order(total_price=100, transaction_fee=1.5)
    order_controller = OrderSummaryController(order=order, order_product_info_list=[])
    assert order_controller.show_order_summary == False

    order_controller = OrderSummaryController(order=order, order_product_info_list=[OrderProductInfo('t', 10, 'waiting')])
    assert order_controller.show_order_summary == True
