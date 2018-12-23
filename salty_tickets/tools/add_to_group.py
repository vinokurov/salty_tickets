from salty_tickets.api.registration_process import get_discount_product_from_form, post_process_discounts
from salty_tickets.config import MONGO, STRIPE_SK
from salty_tickets.dao import TicketsDAO
from salty_tickets.forms import create_event_form
from salty_tickets.models.registrations import TransactionDetails
from salty_tickets.payments import stripe_refund

dao = TicketsDAO(host=MONGO)
event = dao.get_event_by_key('mind_the_shag_2019')


def add_discount_to_payment(payment_id: str, discount_token: str):
    from salty_tickets.views import app
    with app.test_request_context():
        form = create_event_form(event)()
    payment = dao.get_payment_by_id(payment_id)
    form.generic_discount_code.data = discount_token
    discount_product = get_discount_product_from_form(dao, event, form)
    if not discount_product:
        print(f'Can\'t create discount product for code {discount_token}')
        return False

    discounts = discount_product.get_discount(event.tickets, payment, form)
    refund_amount = sum([d.value for d in discounts])

    if not refund_payment(payment, refund_amount, description='Refunded discount'):
        return False

    print(payment.paid_by.full_name, discount_token, 'refunded: ', refund_amount)

    payment.price -= refund_amount

    if payment.discounts:
        payment.discounts += discounts
    else:
        payment.discounts = discounts

    dao.update_payment(payment)
    post_process_discounts(dao, payment, event)


def refund_payment(payment, refund_amount, description='Refund'):
    if refund_amount > payment.paid_price:
        print(f'Refund amount validation failed {refund_amount} > {payment.paid_price}')
        return False
    elif refund_amount <= 0:
        print(f'Invalid refund amount: {refund_amount}')
        return False

    transaction = TransactionDetails(price=-refund_amount, description=description)
    if not stripe_refund(transaction, payment, STRIPE_SK):
        print('Stripe refund failed')
        return False

    return True


def just_refund(payment_id, refund_amount, description):
    payment = dao.get_payment_by_id(payment_id)

    if not refund_payment(payment, refund_amount, description):
        return False

    print(payment.paid_by.full_name, 'refunded: ', refund_amount)
    dao.update_payment(payment)


if __name__ == '__main__':
    payments_to_add = [
        ('5c116fc6b01bad004095ea52', 'grp_92LJd'),
        ('5c110725b01bad003d9a4cd3', 'grp_v4XYd'),
        ('5c1105c7b01bad00409a4cd3', 'grp_beyr2'),
        ('5c110a60b01bad00409a4d18', 'grp_beyr2'),
        ('5c1108b0b01bad002e9a4cd2', 'grp_beyr2'),
        ('5c115f6cb01bad003a95ea18', 'grp_92LJd'),
        ('5c110c5ab01bad00379a4ce6', 'grp_Y4VPe'),
        ('5c110c52b01bad003d9a4d06', 'grp_92LJd'),
        ('5c110761b01bad00289a4cd2', 'OVERSEAS'),
    ]

    for item in payments_to_add:
        add_discount_to_payment(*item)

    refunds = [
        ('5c1109acb01bad00409a4d02', 20, 'Overseas discount refund'),
        ('5c110d50b01bad003a9a4ceb', 55, 'Niomi discount refund'),
        ('5c110a78b01bad00409a4d1e', 5, 'incorrect party pass price refund'),
        ('5c1111b9b01bad0040c8300d', 5, 'incorrect party pass price refund'),
        ('5c111a82b01bad0040c83033', 5, 'incorrect party pass price refund'),
        ('5c114cdbb01bad003a95ea07', 5, 'incorrect party pass price refund'),
    ]

    for item in refunds:
        just_refund(*item)
