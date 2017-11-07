from salty_tickets import config
from salty_tickets.database import db_session
from salty_tickets.models import ORDER_STATUS_PAID, PAYMENT_STATUS_PAID


def process_payment(payment, stripe_token, stripe_sk=None):
    is_success, response = charge(payment, stripe_token, stripe_sk)

    if is_success:
        update_order(payment.order)
        db_session.commit()

    return is_success, response


def charge(payment, stripe_token, stripe_sk=None):
    import stripe
    if not stripe_sk:
        stripe_sk = stripe.api_key = config.STRIPE_SK

    stripe.api_key = stripe_sk

    try:
        charge = stripe.Charge.create(
            amount=stripe_amount(payment),
            currency='gbp',
            description=payment.order.event.name,
            metadata=dict(
                payment_id=payment.id,
                order_id=payment.order.id,
            ),
            source=stripe_token
        )
        print(charge)
        payment.stripe_charge_id = charge['id']
        payment.status = PAYMENT_STATUS_PAID
        return True, charge
    except stripe.CardError as ce:
        # self.stripe_charge_id = charge.get('id', '')
        # self.stripe_charge = jsonify(ce)
        # self.status = ORDER_STATUS_FAILED
        return False, ce

def update_payment_total(payment):
    print([(item.id, item.amount) for item in payment.payment_items if item.amount])
    amount = sum([item.amount for item in payment.payment_items if item.amount])
    payment.amount = amount


def stripe_amount(payment):
    return int((payment.amount + payment.transaction_fee) * 100)


def update_order(user_order):
    total_paid = sum([p.amount for p in user_order.payments])
    user_order.payment_due = user_order.total_price - total_paid

    has_paid = any([p.status == PAYMENT_STATUS_PAID for p in user_order.payments])
    if has_paid:
        user_order.status = ORDER_STATUS_PAID