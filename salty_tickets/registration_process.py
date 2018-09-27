import pickle
from datetime import datetime
from typing import Dict, List

from dataclasses import dataclass, field
from dataclasses_json import DataClassJsonMixin
from flask import session
from salty_tickets import config
from salty_tickets.constants import NEW, SUCCESSFUL, FAILED
from salty_tickets.dao import TicketsDAO
from salty_tickets.emails import send_waiting_list_accept_email, send_payment_status_email
from salty_tickets.forms import create_event_form, StripeCheckoutForm, DanceSignupForm, PartnerTokenCheck
from salty_tickets.models.event import Event
from salty_tickets.models.products import WaitListedPartnerProduct, WorkshopProduct
from salty_tickets.models.registrations import Payment, PersonInfo, PaymentStripeDetails
from salty_tickets.payments import transaction_fee, stripe_charge
from salty_tickets.pricers import ProductPricer
from salty_tickets.tokens import PartnerToken
from salty_tickets.validators import validate_registrations

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
class ProductInfo(DataClassJsonMixin):
    key: str
    title: str
    start_datetime: str
    end_datetime: str
    time: str = None
    level: str = None
    teachers: str = None
    available: int = None
    price: float = None
    info: str = None
    choice: str = None

    @classmethod
    def from_workshop(cls, workshop: WorkshopProduct):
        return cls(
            key=workshop.key,
            title=workshop.name,
            start_datetime=str(workshop.start_datetime),
            end_datetime=str(workshop.end_datetime),
            level=workshop.level,
            teachers=workshop.teachers,
            available=workshop.max_available,
            price=workshop.base_price,
            info=workshop.info
        )


@dataclass
class EventInfo(DataClassJsonMixin):
    name: str
    key: str
    products: List
    layout: Dict

    @classmethod
    def from_event(cls, event):
        return cls(
            name=event.name,
            key=event.key,
            products=[ProductInfo.from_workshop(p) for k, p in event.products.items()
                      if isinstance(p, WorkshopProduct)],
            layout=event.layout
        )


@dataclass
class OrderItem(DataClassJsonMixin):
    name: str
    price: float
    dance_role: str = None
    wait_listed: bool = False
    person: str = None
    partner: str = None


@dataclass
class OrderSummary(DataClassJsonMixin):
    total_price: float = 0
    transaction_fee: float = 0
    total: float = 0
    items: List[OrderItem] = field(default_factory=list)

    @classmethod
    def from_payment(cls, event: Event, payment: Payment):
        items = []
        for reg in payment.registrations:
            items.append(OrderItem(
                name=event.products[reg.product_key].name,
                price=reg.price,
                person=reg.person.full_name,
                partner=reg.partner.full_name if reg.partner else None,
                dance_role=reg.dance_role,
                wait_listed=reg.wait_listed
            ))

        return cls(total_price=payment.price, transaction_fee=payment.transaction_fee,
                   total=payment.total_amount, items=items)


@dataclass
class StripeData(DataClassJsonMixin):
    amount: int = 0
    email: str = ''

    @classmethod
    def from_payment(cls, payment: Payment):
        if len(payment.registrations):
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
    def from_payment(cls, event: Event, payment: Payment, errors: List):
        return cls(
            stripe=StripeData.from_payment(payment),
            order_summary=OrderSummary.from_payment(event, payment),
            errors=errors,
        )

    def __post_init__(self):
        if not self.errors and len(self.order_summary.items) > 0:
            self.disable_checkout = False


@dataclass
class PaymentResult(DataClassJsonMixin):
    success: bool
    complete: bool = True
    error_message: str = None
    payee_id: str = None
    payment_id: str = None

    @classmethod
    def from_paid_payment(cls, paid_payment: Payment):
        payment_result = PaymentResult(
            success=(paid_payment.status == SUCCESSFUL),
            payment_id=str(paid_payment.id),
            complete=(paid_payment.status != NEW)
        )
        if not payment_result.success:
            if paid_payment.stripe and paid_payment.stripe.charge:
                payment_result.error_message = paid_payment.stripe.charge.get('message')
        else:
            payment_result.payee_id = str(paid_payment.paid_by.id)
        return payment_result


@dataclass
class PartnerTokenCheckResult(DataClassJsonMixin):
    success: bool
    error: str = ''
    name: str = ''
    roles: Dict = None

    @classmethod
    def from_registration_list(cls, registrations):
        active_registrations = [r for r in registrations if r.active and not r.partner and r.dance_role]
        if not active_registrations:
            return cls(success=False, error='Token is not valid for this event')

        return cls(success=True, name=active_registrations[0].person.full_name,
                   roles={r.product_key: r.dance_role for r in active_registrations})


def get_payment_from_form(event: Event, form, extra_registrations=None):
    registrations = []
    for prod_key, prod in event.products.items():
        registrations += prod.parse_form(form)

    # apply extra registrations
    if extra_registrations is not None:
        applied_registrations = []
        for reg in [r for r in registrations if not r.partner]:
            product = event.products[reg.product_key]
            if isinstance(product, WaitListedPartnerProduct):
                applied_reg = product.apply_extra_partner(reg, extra_registrations)
                if applied_reg:
                    applied_registrations.append(applied_reg)

    # add prices
    pricer = ProductPricer.from_event(event)
    pricer.price_all(registrations)

    prices = [r.price for r in registrations if r.price is not None]
    if prices:
        total_price = sum(prices)
        fee = transaction_fee(total_price)
    else:
        total_price = 0.0
        fee = 0.0
    payment = Payment(
        price=total_price,
        paid_by=registrations[0].registered_by if len(registrations) else None,
        transaction_fee=fee,
        registrations=registrations,
        status=NEW,
        info_items=[(event.products[r.product_key].item_info(r), r.price) for r in registrations]
    )

    if extra_registrations is not None:
        payment.extra_registrations = applied_registrations

    return payment


def get_extra_registrations_from_partner_token(dao: TicketsDAO, event: Event, form):
    if form.partner_token.data:
        partner = PartnerToken().deserialize(dao, form.partner_token.data)
        return dao.query_registrations(event.key, partner)


def do_price(dao: TicketsDAO, event_key: str):
    event = dao.get_event_by_key(event_key)
    form = create_event_form(event)()
    valid = form.validate_on_submit()

    extra_registrations = get_extra_registrations_from_partner_token(dao, event, form)
    if extra_registrations:
        payment = get_payment_from_form(event, form, extra_registrations)
    else:
        payment = get_payment_from_form(event, form)

    if payment:
        errors = {}
        errors.update(validate_registrations(event, payment.registrations))
        errors.update(form.errors)
        return PricingResult.from_payment(event, payment, errors)


def do_checkout(dao: TicketsDAO, event_key: str):
    event = dao.get_event_by_key(event_key)
    form = create_event_form(event)()
    valid = form.validate_on_submit()

    extra_registrations = get_extra_registrations_from_partner_token(dao, event, form)
    if extra_registrations:
        payment = get_payment_from_form(event, form, extra_registrations)
    else:
        payment = get_payment_from_form(event, form)

    if payment:
        errors = {}
        errors.update(validate_registrations(event, payment.registrations))
        errors.update(form.errors)
        pricing_result = PricingResult.from_payment(event, payment, errors)
        if valid and not errors and not pricing_result.disable_checkout:
            # dao.add_payment(payment, event, register=True)
            # pricing_result.payment_id = str(payment.id)
            session['payment'] = payment
            session['event_key'] = event_key
            print(session)
            print(session.keys())
            print(session.sid)
            pricing_result.checkout_success = not pricing_result.disable_checkout
            # pickle_str = pickle.dumps(pricing_result)
            # session['pricing_result'] = pickle_str
        return pricing_result


def do_pay(dao: TicketsDAO):
    form = StripeCheckoutForm()
    # if form.validate_on_submit():

    # print(session)
    # print(session.keys())
    # print(session.sid)
    payment = session.get('payment')
    event_key = session.get('event_key')
    if payment and event_key:
        # payment = dao.get_payment_by_id(form.payment_id.data)
        if payment is None or payment.status not in [NEW, FAILED]:
            return PaymentResult(success=False, error_message='Invalid payment id')

        event = dao.get_event_by_key(event_key)
        payment.description = event.name
        payment.stripe = PaymentStripeDetails(source=form.stripe_token.data)

        if hasattr(payment, 'id') and payment.id:
            dao.update_payment(payment)
        else:
            dao.add_payment(payment, event, register=True)

        success = stripe_charge(payment, config.STRIPE_SK)
        dao.update_payment(payment)
        if success:
            session.pop('payment')
            session.pop('event_key')
            for reg in payment.registrations:
                reg.active = True
                dao.update_registration(reg)

            # TODO: make it nicer - with emails, etc.
            if payment.extra_registrations:
                for reg in payment.registrations:
                    for extra_reg in payment.extra_registrations:
                        if extra_reg.active and (reg.product_key == extra_reg.product_key):
                            extra_reg.partner = reg.registered_by
                            extra_reg.wait_listed = reg.wait_listed
                            dao.update_registration(extra_reg)

            registration_post_process(dao, payment)

        return PaymentResult.from_paid_payment(payment)

    return PaymentResult(success=False, error_message='Invalid payment id')


def do_get_payment_status(dao: TicketsDAO):
    form = StripeCheckoutForm()
    if form.validate_on_submit():
        payment = dao.get_payment_by_id(form.payment_id.data)
        if payment.stripe is None or payment.stripe.source is None:
            return PaymentResult(success=False, complete=False, error_message='Payment not initiated yet')
        elif payment.stripe.source['id'] == form.stripe_token.data['id']:
            return PaymentResult.from_paid_payment(payment)

        print(payment.stripe.source, form.stripe_token.data)

    print(form.errors)
    return PaymentResult(success=False, error_message='Access denied to see payment status')


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


def do_check_partner_token(dao: TicketsDAO):
    form = PartnerTokenCheck()
    if form.validate_on_submit():
        try:
            partner = PartnerToken().deserialize(dao, form.partner_token.data)
        except Exception as e:
            return PartnerTokenCheckResult(success=False, error='Invalid token')
        if partner:
            partner_registrations = dao.query_registrations(event=form.event_key.data, person=partner)
            return PartnerTokenCheckResult.from_registration_list(partner_registrations)
    return PartnerTokenCheckResult.from_registration_list([])

