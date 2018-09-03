from datetime import datetime

from salty_tickets.constants import NEW, FAILED, SUCCESSFUL
from salty_tickets.models.order import Payment


def test_payment():
    before = datetime.utcnow()
    payment = Payment(price=10)
    after = datetime.utcnow()
    assert payment.status == NEW
    assert before <= payment.date <= after
