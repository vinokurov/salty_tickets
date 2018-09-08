import json
from typing import Dict, List

from dataclasses import dataclass, field
from dataclasses_json import DataClassJsonMixin
from flask import jsonify
from salty_tickets.constants import NEW, SUCCESSFUL, FAILED
from salty_tickets.dao import TicketsDAO
from salty_tickets.emails import send_waiting_list_accept_email, send_payment_status_email
from salty_tickets.forms import get_primary_personal_info_from_form, get_partner_personal_info_from_form, \
    create_event_form, StripeCheckoutForm
from salty_tickets.models.event import Event
from salty_tickets.models.products import WaitListedPartnerProduct
from salty_tickets.models.registrations import Payment, PersonInfo, PaymentStripeDetails
from salty_tickets.payments import transaction_fee, stripe_charge
from salty_tickets.pricers import ProductPricer

"""
Before chackout:
    - get form data
    - price products, validate fields
    - return JSON with prices, field validation, etc

Checkout:
    - generate Payment instance (with prices)
    - save with status new
    - send stripe details (amount, stripe token), payment id
    - user goes through stripe dialog in browser, gets stripe token
    - user publishes form with stripe token
    - check payment status (using) stripe
    - if payment failed: show response
    - if payment passed: update statuses, rebalance, send emails
    - user polls status - ready -> thank you, order details 
"""


@dataclass
class OrderSummary(DataClassJsonMixin):
    total_price: float = 0
    transaction_fee: float = 0
    total: float = 0
    items: List[List] = field(default_factory=list)

    @classmethod
    def from_payment(cls, payment: Payment):
        return cls(total_price=payment.price, transaction_fee=payment.transaction_fee,
                   total=payment.total_amount, items=payment.info_items)


@dataclass
class StripeData(DataClassJsonMixin):
    amount: int = 0
    email: str = ''

    @classmethod
    def from_payment(cls, payment: Payment):
        amount = int(payment.total_amount * 100)
        return cls(amount=amount, email=payment.paid_by.email)


@dataclass
class PricingResult(DataClassJsonMixin):
    """These are AJAX objects containing result of pricing"""
    errors: Dict[str, str] = field(default_factory=dict)
    stripe: StripeData = field(default_factory=dict)
    order_summary: OrderSummary = field(default_factory=OrderSummary)
    disable_checkout: bool = True
    checkout_success: bool = False
    payment_id: str = ''

    @classmethod
    def from_payment(cls, payment: Payment, form):
        return cls(
            stripe=StripeData.from_payment(payment),
            order_summary=OrderSummary.from_payment(payment),
        )


@dataclass
class PaymentResult(DataClassJsonMixin):
    success: bool
    error_message: str = None
    payee_id: str = None
    payment_id: str = None

    @classmethod
    def from_paid_payment(cls, paid_payment: Payment):
        payment_result = PaymentResult(
            success=(paid_payment.status == SUCCESSFUL),
            payment_id=str(paid_payment.id),
        )
        if not payment_result.success:
            payment_result.error_message = paid_payment.stripe.charge.get('message')
        else:
            payment_result.payee_id = str(paid_payment.paid_by.id)
        return payment_result


def get_payment_from_form(event: Event, form):
    registrations = []
    for prod_key, prod in event.products.items():
        registrations += prod.parse_form(form)

    # add prices
    pricer = ProductPricer.from_event(event)
    pricer.price_all(registrations)

    total_price = sum([r.price for r in registrations])
    payment = Payment(
        price=total_price,
        paid_by=registrations[0].registered_by,
        transaction_fee=transaction_fee(total_price),
        registrations=registrations,
        status=NEW,
        info_items=[(event.products[r.product_key].item_info(r), r.price) for r in registrations]
    )
    return payment


def do_price(dao: TicketsDAO, event_key: str):
    event = dao.get_event_by_key(event_key)
    form = create_event_form(event)()
    if form.validate_on_submit():
        payment = get_payment_from_form(event, form)
        if payment:
            pricing_result_json = PricingResult.from_payment(payment, form).to_json()
            return jsonify(json.loads(pricing_result_json))
    else:
        #TODO
        pass


def do_checkout(dao: TicketsDAO, event_key: str):
    event = dao.get_event_by_key(event_key)
    form = create_event_form(event)()
    if form.validate_on_submit():
        payment = get_payment_from_form(event, form)
        if payment:
            dao.add_payment(payment, event, register=True)
            pricing_result = PricingResult.from_payment(payment, form)
            pricing_result.payment_id = str(payment.id)
            pricing_result_json = pricing_result.to_json()
            return jsonify(json.loads(pricing_result_json))
    else:
        #TODO
        pass


def do_pay(dao: TicketsDAO):
    form = StripeCheckoutForm()
    if form.validate_on_submit():
        payment = dao.get_payment_by_id(form.payment_id.data)
        if payment is None or payment.status not in [NEW, FAILED]:
            payment_result = PaymentResult(success=False, error_message='Invalid payment id')
        else:
            payment.stripe = PaymentStripeDetails(source=form.stripe_token.data)
            dao.update_payment(payment)

            success = stripe_charge(payment, 'sk_123')
            dao.update_payment(payment)
            if success:
                for reg in payment.registrations:
                    reg.active = True
                    dao.update_registration(reg)

                    registration_post_process(dao, payment)

            payment_result = PaymentResult.from_paid_payment(payment)

        return jsonify(json.loads(payment_result.to_json()))


def balance_event_waiting_lists(dao: TicketsDAO, event: Event):
    balanced_registrations = []
    event = dao.get_event_by_key(event.key)
    for product_key, product in event.products.items():
        if isinstance(product, WaitListedPartnerProduct):
            if product.waiting_list.has_waiting_list:
                for registration in product.balance_waiting_list():
                    balanced_registrations.append(registration)
                    dao.update_registration(registration)
    # send emails
    if balanced_registrations:
        unique_persons = set([r.person for r in balanced_registrations])
        for person in unique_persons:
            send_waiting_list_accept_email(dao, person, event)


def registration_post_process(dao: TicketsDAO, payment: Payment):
    """send emails, ballance waiting lists"""
    event = dao.get_payment_event(payment)
    send_payment_status_email(dao, payment, event)
    balance_event_waiting_lists(dao, event)
