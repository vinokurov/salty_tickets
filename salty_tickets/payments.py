from contextlib import contextmanager

from salty_tickets import config
# from salty_tickets.to_delete.database import db_session
# from salty_tickets.to_delete.sql_models import ORDER_STATUS_PAID, PAYMENT_STATUS_PAID, Payment, PaymentItem
from salty_tickets.constants import SUCCESSFUL, FAILED
from salty_tickets.models.registrations import Payment, TransactionDetails
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


@contextmanager
def stripe_session(stripe_sk):
    import stripe
    stripe.api_key = stripe_sk
    yield stripe
    stripe.api_key = None


def make_line_items(transaction: TransactionDetails, payment: Payment):
    line_items = [{
        'name': payment.description,
        # 'description': payment.description,
        'images': [
            'https://static.wixstatic.com/media/eb4a35_fe468602010940e3b81d45032c760bf8~mv2.jpg/v1/fill/w_851,h_315,al_c/eb4a35_fe468602010940e3b81d45032c760bf8~mv2.jpg'],
        'amount': stripe_amount(0) + 1,
        'currency': 'gbp',
        'quantity': 1,
    }]
    line_items += [{'name': n, 'amount': stripe_amount(a) + 1, 'currency': 'gbp', 'quantity': 1} for (n, a) in payment.info_items]
    line_items += [{
        'name': 'Booking fee',
        'amount': stripe_amount(transaction.transaction_fee),
        'currency': 'gbp',
        'quantity': 1,
    }]
    print(line_items)
    return line_items


def make_items_description(transaction: TransactionDetails, payment: Payment) -> str:
    items = payment.info_items + [('Booking fee', transaction.transaction_fee)]
    return '\r\n\r\n'.join(f'£{round(a,2)}\t{d}' for (d, a) in items)


def stripe_session_create(transaction: TransactionDetails, payment: Payment, stripe_sk, url_success: str, url_cancel: str):
    if transaction.price > 0:
        amount = transaction.price + transaction.transaction_fee
        with stripe_session(stripe_sk) as sp:
            stripe_session_obj = sp.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'name': payment.description,
                    # 'description': make_items_description(transaction, payment),
                    'images': ['https://static.wixstatic.com/media/eb4a35_fe468602010940e3b81d45032c760bf8~mv2.jpg/v1/fill/w_851,h_315,al_c/eb4a35_fe468602010940e3b81d45032c760bf8~mv2.jpg'],
                    'amount': stripe_amount(amount),
                    'currency': 'gbp',
                    'quantity': 1,
                }],
                success_url=url_success,
                cancel_url=url_cancel,
                customer_email=payment.paid_by.email,
                client_reference_id=str(payment.id),
                payment_intent_data=dict(
                    metadata=dict(
                        payment_id=str(payment.id),
                        # items=', '.join(payment.info_items),
                    ),
                    receipt_email=payment.paid_by.email,
                    description=payment.description,
                )
            )
        transaction.stripe_session_obj = stripe_session_obj
        transaction.stripe_session_id = stripe_session_obj['id']
    payment.transactions.append(transaction)
    return True


def stripe_is_session_successful(transaction: TransactionDetails, stripe_sk):
    with stripe_session(stripe_sk) as sp:
        session_obj = sp.checkout.Session.retrieve(transaction.stripe_session_id)
        intent = sp.PaymentIntent.retrieve(session_obj.payment_intent)
        if intent.status == 'succeeded':
            transaction.success = True
            return True
        else:
            transaction.success = False
            transaction.error_response = intent.last_payment_error
            return False


def stripe_charge(transaction: TransactionDetails, payment: Payment, stripe_sk):
    if transaction.price > 0:
        amount = transaction.price + transaction.transaction_fee
        try:
            with stripe_session(stripe_sk) as sp:
                charge = sp.Charge.create(
                    amount=stripe_amount(amount),
                    currency='gbp',
                    description=payment.description,
                    metadata=dict(
                        payment_id=str(payment.id),
                        # items=', '.join(payment.info_items),
                    ),
                    source=payment.stripe.token_id,
                    receipt_email=payment.paid_by.email,
                )
            payment.stripe.charges.append(charge.get('id'))
            transaction.stripe_charge_id = charge.get('id')
        except CardError as e:
            payment.stripe.error_response = e.json_body
            payment.status = FAILED
            transaction.success = False
            transaction.error_response = e.json_body
            payment.transactions.append(transaction)
            return False

    payment.status = SUCCESSFUL
    transaction.success = True
    payment.transactions.append(transaction)
    return True


def stripe_create_customer(payment: Payment, stripe_sk):
    try:
        with stripe_session(stripe_sk) as sp:
            customer = sp.Customer.create(
                source=payment.stripe.token_id,
                email=payment.paid_by.email,
                description=payment.paid_by.full_name,
                metadata=dict(
                    payment_id=str(payment.id),
                    full_name=payment.paid_by.full_name,
                    info=payment.description,
                )
            )

            payment.stripe.customer_id = customer.get('id')
            # payment.stripe.customer_source_id = customer['sources']['data'][0]['id']

        return True
    except CardError as e:
        payment.stripe.error_response = e.json_body
        payment.status = FAILED
        return False


def stripe_charge_customer(transaction: TransactionDetails, payment: Payment, stripe_sk):
    if transaction.price > 0:
        amount = transaction.price + transaction.transaction_fee
        try:
            with stripe_session(stripe_sk) as sp:
                charge = sp.Charge.create(
                    amount=stripe_amount(amount),
                    currency='gbp',
                    description=payment.description,
                    metadata=dict(
                        payment_id=str(payment.id),
                        # items=', '.join(payment.info_items),
                    ),
                    customer=payment.stripe.customer_id,
                    # source=payment.stripe.customer_source_id,
                    receipt_email=payment.paid_by.email,
                )

            payment.stripe.charges.append(charge.get('id'))
            transaction.stripe_charge_id = charge.get('id')
        except CardError as e:
            if not payment.transactions:
                payment.stripe.error_response = e.json_body
                payment.status = FAILED
            transaction.success = False
            transaction.error_response = e.json_body
            payment.transactions.append(transaction)
            return False

    payment.status = SUCCESSFUL
    transaction.success = True
    payment.transactions.append(transaction)
    return True


def stripe_refund(transaction: TransactionDetails, payment: Payment, stripe_sk, reason: str = 'requested_by_customer'):
    amount = transaction.price + transaction.transaction_fee
    with stripe_session(stripe_sk) as sp:
        charge_id = payment.stripe.charges[0]
        refund = sp.Refund.create(
            charge=charge_id,
            amount=-stripe_amount(amount),
            reason=reason,
        )
        payment.stripe.charges.append(refund.get('id'))
        transaction.success = True
        transaction.stripe_charge_id = refund.get('id')
        payment.transactions.append(transaction)
        return True


def update_payment_total(payment):
    # amount = sum([item.amount for item in payment.payment_items if item.amount])
    # payment.amount = amount
    pass


# def stripe_amount(payment: Payment):
#     return int(payment.total_amount * 100)


def stripe_amount(amount):
    return int(amount * 100)


def update_order(user_order):
    # total_paid = sum([p.amount for p in user_order.payments])
    # user_order.payment_due = user_order.total_price - total_paid
    #
    # has_paid = any([p.status == PAYMENT_STATUS_PAID for p in user_order.payments])
    # if has_paid:
    #     user_order.status = ORDER_STATUS_PAID
    pass


def transaction_fee(*prices):
    total_fee = 0
    for price in prices:
        if price > 0:
            fee = price * 0.015 + 0.2
            total_fee += round(fee, 2)
    return round(total_fee, 2)


def get_remaining_payment(amount):
    # fee = transaction_fee(amount)
    # payment = Payment(
    #     amount=amount,
    #     transaction_fee=fee,
    # )
    # payment.payment_items.append(PaymentItem(amount=amount, description='Remaining payment'))
    # return payment
    pass
