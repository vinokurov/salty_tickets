from datetime import datetime

from salty_tickets.constants import NEW, FAILED, SUCCESSFUL
from salty_tickets.models.registrations import Payment, Person


def test_payment():
    before = datetime.utcnow()
    payment = Payment(price=10, paid_by=Person(full_name='Mr One', email='mr.one@one.com'))
    after = datetime.utcnow()
    assert payment.status == NEW
    assert before <= payment.date <= after
