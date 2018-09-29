from salty_tickets.constants import NEW, SUCCESSFUL
from salty_tickets.models.registrations import Payment, PersonInfo, PaymentStripeDetails
from salty_tickets.payments import stripe_charge, transaction_fee, stripe_amount, stripe_create_customer, \
    stripe_charge_customer
from stripe import Charge, Customer


def test_stripe_charge_success(mock_stripe):
    stripe_pk = 'pk_mock'
    payment = Payment(price=10, transaction_fee=0.5, description='DESCR', status=NEW,
                      stripe=PaymentStripeDetails(token_id='tok_123'),
                      info_items=['a', 'b'], paid_by=PersonInfo(full_name='Alex', email='alex@a.b'))
    payment.id = 'a123b'
    charge = Charge(id='ch_123')
    mock_stripe.Charge.create.return_value = Charge(id='ch_123')
    res = stripe_charge(payment, stripe_pk)
    assert res
    assert payment.status == SUCCESSFUL
    assert payment.stripe.charges == [charge.to_dict()['id']]
    mock_stripe.Charge.create.assert_called_with(amount=1050, currency='gbp', description='DESCR',
                                                 metadata={'payment_id': 'a123b'},
                                                 source='tok_123', receipt_email='alex@a.b')


def test_stripe_create_customer(mock_stripe):
    stripe_pk = 'pk_mock'
    payment = Payment(price=10, transaction_fee=0.5, description='DESCR', status=NEW,
                      stripe=PaymentStripeDetails(token_id='tok_123'),
                      info_items=['a', 'b'], paid_by=PersonInfo(full_name='Alex', email='alex@a.b'))
    payment.id = 'a123b'
    mock_stripe.Customer.create.return_value = Customer(id='cus_123')
    res = stripe_create_customer(payment, stripe_pk)
    assert res
    assert payment.stripe.customer_id == 'cus_123'
    mock_stripe.Customer.create.assert_called_with(source='tok_123', email='alex@a.b',
                                                   description='Alex',
                                                   metadata={
                                                       'payment_id': 'a123b',
                                                       'full_name': 'Alex',
                                                       'info': 'DESCR'
                                                   })


def test_stripe_charge_customer(mock_stripe):
    stripe_pk = 'pk_mock'
    payment = Payment(price=10, transaction_fee=0.5, description='DESCR', status=NEW,
                      stripe=PaymentStripeDetails(token_id='tok_123', customer_id='cus_123'),
                      info_items=['a', 'b'], paid_by=PersonInfo(full_name='Alex', email='alex@a.b'))
    payment.id = 'a123b'
    charge = Charge(id='ch_123')
    mock_stripe.Charge.create.return_value = Charge(id='ch_123')
    res = stripe_charge_customer(payment, stripe_pk)
    assert res
    assert payment.status == SUCCESSFUL
    assert payment.stripe.charges == [charge.to_dict()['id']]
    mock_stripe.Charge.create.assert_called_with(amount=1050, currency='gbp', description='DESCR',
                                                 metadata={'payment_id': 'a123b'},
                                                 customer='cus_123', receipt_email='alex@a.b')


def test_transaction_fee():
    assert 0 == transaction_fee(0)
    assert 0.22 == transaction_fee(1.0)
    assert 0.20 == transaction_fee(0.1)
    assert 1.70 == transaction_fee(100)
    assert 0 == transaction_fee(-100)

    assert 0.42 == transaction_fee(1.0, 0.1)
    assert 0.42 == transaction_fee(1.0, 0.1, 0)


def test_stripe_amount():
    assert 10100 == stripe_amount(101.0)
    assert 10010 == stripe_amount(100.1)
