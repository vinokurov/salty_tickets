from salty_tickets.constants import NEW, SUCCESSFUL
from salty_tickets.models.registrations import Payment, PersonInfo, PaymentStripeDetails
from salty_tickets.payments import stripe_charge
from stripe import Charge


def test_stripe_charge_success(mock_stripe):
    stripe_pk = 'pk_mock'
    payment = Payment(price=10, transaction_fee=0.5, description='DESCR', status=NEW,
                      stripe=PaymentStripeDetails(token_id='tok_123'),
                      info_items=['a', 'b'], paid_by=PersonInfo(full_name='Alex', email='alex@a.b'))
    payment.id = 'a123b'
    # charge = {'id': 'ch_123', 'test': 'stripe'}
    charge = Charge(id='ch_123')
    mock_stripe.Charge.create.return_value = Charge(id='ch_123')
    res = stripe_charge(payment, stripe_pk)
    assert res
    assert payment.status == SUCCESSFUL
    assert payment.stripe.charge_id == charge.to_dict()['id']
    mock_stripe.Charge.create.assert_called_with(amount=1050, currency='gbp', description='DESCR',
                                                 metadata={'payment_id': 'a123b',
                                                           # 'items': ['a', 'b']
                                                           },
                                                 source='tok_123', receipt_email='alex@a.b')
