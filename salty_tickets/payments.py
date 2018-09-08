from salty_tickets import config
# from salty_tickets.to_delete.database import db_session
# from salty_tickets.to_delete.sql_models import ORDER_STATUS_PAID, PAYMENT_STATUS_PAID, Payment, PaymentItem
from salty_tickets.constants import SUCCESSFUL, FAILED
from salty_tickets.models.registrations import Payment
from stripe.error import CardError


def process_payment(payment, stripe_token, stripe_sk=None):
    # if payment.amount > 0:
    #     is_success, response = stripe_charge(payment, stripe_token, stripe_sk)
    # else:
    #     is_success, response = True, 'Don\'t need to pay'
    #     payment.status = PAYMENT_STATUS_PAID
    #
    # if is_success:
    #     update_order(payment.order)
    #     db_session.commit()
    #
    # return is_success, response
    pass


def stripe_session(stripe_sk):
    import stripe
    stripe.api_key = stripe_sk
    yield stripe
    stripe.api_key = None


def stripe_charge(payment: Payment, stripe_sk):
    try:
        with stripe_session(stripe_sk) as sp:
            charge = sp.Charge.create(
                amount=stripe_amount(payment),
                currency='gbp',
                description=payment.description,
                metadata=dict(
                    payment_id=str(payment.id),
                    items=payment.info_items,
                ),
                source=payment.stripe.source,
                receipt_email=payment.paid_by.email,
            )
        print(charge)
        payment.stripe.charge = charge
        payment.stripe.charge_id = charge.get('id')
        payment.status = SUCCESSFUL
        return True
    except CardError as e:
        payment.stripe_details = e.json_body
        payment.status = FAILED
        return False


def update_payment_total(payment):
    # amount = sum([item.amount for item in payment.payment_items if item.amount])
    # payment.amount = amount
    pass


def stripe_amount(payment: Payment):
    return int(payment.total_amount * 100)


def update_order(user_order):
    # total_paid = sum([p.amount for p in user_order.payments])
    # user_order.payment_due = user_order.total_price - total_paid
    #
    # has_paid = any([p.status == PAYMENT_STATUS_PAID for p in user_order.payments])
    # if has_paid:
    #     user_order.status = ORDER_STATUS_PAID
    pass


def transaction_fee(price):
    if price > 0:
        return price * 0.015 + 0.2
    else:
        return 0


def get_remaining_payment(amount):
    # fee = transaction_fee(amount)
    # payment = Payment(
    #     amount=amount,
    #     transaction_fee=fee,
    # )
    # payment.payment_items.append(PaymentItem(amount=amount, description='Remaining payment'))
    # return payment
    pass
