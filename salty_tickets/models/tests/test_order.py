from datetime import datetime

from salty_tickets.constants import PAYMENT_STATUS
from salty_tickets.models.order import Payment, Purchase, PurchaseItem, Order


def test_payment():
    before = datetime.utcnow()
    payment = Payment(price=10)
    after = datetime.utcnow()
    assert payment.status == PAYMENT_STATUS.NEW
    assert before <= payment.date <= after


def test_purchase():
    purchase = Purchase()
    assert purchase.total_price == 0

    purchase_items = [
        PurchaseItem('Item 1', 'prod1', price=10.0),
        PurchaseItem('Item 2', 'prod2', price=15.0),
    ]
    purchase = Purchase(purchase_items=purchase_items)
    assert purchase.total_price == 25.0


def test_order():
    purchase = Purchase(purchase_items=[
        PurchaseItem('Item 1', 'prod1', price=10.0),
        PurchaseItem('Item 2', 'prod2', price=15.0),
    ])
    payments = [
        Payment(price=10.0, transaction_fee=0.5, status=PAYMENT_STATUS.FAILED),
        Payment(price=10.0, transaction_fee=0.5, status=PAYMENT_STATUS.OK),
    ]
    order = Order('Mr Dancer', 'dance@gmail.com', purchases=[purchase], payments=payments)
    assert order.total_price == 25.0
    assert order.total_paid == 10.0
