import pytest
from salty_tickets.controllers import OrderProductInfo, OrderSummaryController, OrderProductController
from salty_tickets.models import ORDER_PRODUCT_STATUS_WAITING, ORDER_PRODUCT_STATUS_ACCEPTED, Order, OrderProduct, \
    Product
from mock import Mock


def test_OrderProductController_price():
    order_product = Mock(spec=OrderProduct)
    order_product.price = 10.123
    controller = OrderProductController(order_product)
    assert controller.price == '10.12'


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


# def test_OrderSummaryController_price_format():
#     assert OrderSummaryController.price_format(10) == '10.00'
#     assert OrderSummaryController.price_format(10.123) == '10.12'
#     assert OrderSummaryController.price_format(10.229) == '10.23'


def test_OrderSummaryController_transaction_fee():
    order = Order(total_price=100, transaction_fee=1.5)
    order_controller = OrderSummaryController(order=order)
    assert order_controller.transaction_fee == '1.50'


def test_OrderSummaryController_total_price():
    order = Order(total_price=100, transaction_fee=1.5)
    order_controller = OrderSummaryController(order=order)
    assert order_controller.total_price == '101.50'


def test_OrderSummaryController_show_order_summary():
    order = Order(total_price=100, transaction_fee=1.5)
    order_controller = OrderSummaryController(order=order)
    assert order_controller.show_order_summary == False

    product = Product('Test', 'Test')
    order.order_products.append(OrderProduct(product, 10))
    order_controller = OrderSummaryController(order=order)
    assert order_controller.show_order_summary == True
