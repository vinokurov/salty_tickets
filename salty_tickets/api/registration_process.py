import pickle
from datetime import datetime
from typing import Dict, List, Optional

from dataclasses import dataclass, field
from dataclasses_json import DataClassJsonMixin
from flask import session
from salty_tickets import config
from salty_tickets.constants import NEW, SUCCESSFUL, FAILED
from salty_tickets.dao import TicketsDAO
from salty_tickets.emails import send_waiting_list_accept_email, send_registration_confirmation
from salty_tickets.forms import create_event_form, StripeCheckoutForm, DanceSignupForm, PartnerTokenCheck
from salty_tickets.models.event import Event
from salty_tickets.models.products import WaitListedPartnerProduct, WorkshopProduct
from salty_tickets.models.registrations import Payment, PersonInfo, PaymentStripeDetails, ProductRegistration
from salty_tickets.payments import transaction_fee, stripe_charge, stripe_create_customer, stripe_charge_customer
from salty_tickets.pricers import ProductPricer
from salty_tickets.tokens import PartnerToken, PaymentId
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
class ProductWaitingListInfo(DataClassJsonMixin):
    leader: Optional[int] = None
    follower: Optional[int] = None
    couple: Optional[int] = None


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
    waiting_list: Optional[ProductWaitingListInfo] = None

    @classmethod
    def from_workshop(cls, workshop: WorkshopProduct):
        available = workshop.max_available - workshop.waiting_list.total_accepted
        return cls(
            key=workshop.key,
            title=workshop.name,
            start_datetime=str(workshop.start_datetime),
            end_datetime=str(workshop.end_datetime),
            level=workshop.level,
            teachers=workshop.teachers,
            available=available,
            price=workshop.base_price,
            info=workshop.info,
            waiting_list=ProductWaitingListInfo(**workshop.waiting_list.waiting_stats)
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

    pay_all_now: bool = True

    pay_now: Optional[float] = None
    pay_now_fee: Optional[float] = None
    pay_now_total: Optional[float] = None

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

        return cls(
            total_price=payment.price,
            transaction_fee=payment.transaction_fee,
            total=payment.total_amount,
            pay_all_now=payment.pay_all_now,
            pay_now=payment.first_pay_amount,
            pay_now_fee=payment.first_pay_fee,
            pay_now_total=payment.first_pay_total,
            items=items,
        )


@dataclass
class StripeData(DataClassJsonMixin):
    amount: int = 0
    email: str = ''

    @classmethod
    def from_payment(cls, payment: Payment):
        if len(payment.registrations):
            amount = int(payment.first_pay_total * 100)
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
    def from_payment(cls, event: Event, payment: Payment, errors: Dict):
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
    pmt_token: str = None

    @classmethod
    def from_paid_payment(cls, paid_payment: Payment):
        payment_result = PaymentResult(
            success=(paid_payment.status == SUCCESSFUL),
            payment_id=str(paid_payment.id),
            complete=(paid_payment.status != NEW)
        )
        if not payment_result.success:
            payment_result.error_message = 'Payment failed'
        else:
            payment_result.payee_id = str(paid_payment.paid_by.id)
            payment_result.pmt_token = PaymentId().serialize(paid_payment)
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

    payment = Payment(
        paid_by=registrations[0].registered_by if len(registrations) else None,
        registrations=registrations,
        status=NEW,
        info_items=[(event.products[r.product_key].item_info(r), r.price) for r in registrations],
        pay_all_now=form.pay_all.data,
    )

    set_payment_totals(payment)

    if extra_registrations is not None:
        payment.extra_registrations = applied_registrations

    return payment


def get_extra_registrations_from_partner_token(dao: TicketsDAO, event: Event, form):
    if form.partner_token.data:
        partner = PartnerToken().deserialize(dao, form.partner_token.data)
        return dao.query_registrations(event, partner)


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
            session['payment'] = pickle.dumps(payment)
            session['event_key'] = event_key
            pricing_result.checkout_success = not pricing_result.disable_checkout
        return pricing_result


def do_pay(dao: TicketsDAO):
    form = StripeCheckoutForm()
    if form.validate_on_submit():
        payment_pickle = session.get('payment')
        payment = pickle.loads(payment_pickle) if payment_pickle else None
        event_key = session.get('event_key')
        if payment and event_key:
            if payment is None or payment.status not in [NEW, FAILED]:
                return PaymentResult(success=False, error_message='Invalid payment id')

            event = dao.get_event_by_key(event_key)
            payment.description = event.name
            stripe_token_id = form.stripe_token.data.get('id')
            payment.stripe = PaymentStripeDetails(token_id=stripe_token_id)

            if hasattr(payment, 'id') and payment.id:
                dao.update_payment(payment)
            else:
                dao.add_payment(payment, event, register=True)

            success = process_first_payment(payment)
            dao.update_payment(payment)
            session['payment'] = pickle.dumps(payment)

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
                                take_existing_registration_off_waiting_list(dao, extra_reg, reg.registered_by)

                registration_post_process(dao, payment)

            return PaymentResult.from_paid_payment(payment)

    return PaymentResult(success=False, error_message='Invalid payment id')


def process_first_payment(payment):
    if payment.pay_all_now or (payment.first_pay_amount == payment.price):
        if stripe_charge(payment, config.STRIPE_SK, payment.total_amount):
            # update paid prices on all registrations
            for reg in payment.registrations:
                reg.paid_price = reg.price
            return True
    else:
        if stripe_create_customer(payment, config.STRIPE_SK):
            if payment.first_pay_amount > 0:
                if stripe_charge_customer(payment, config.STRIPE_SK, payment.first_pay_total):
                    # update paid prices on accepted registrations
                    for reg in payment.registrations:
                        if not reg.wait_listed:
                            reg.paid_price = reg.price
                    return True
            else:
                payment.status = SUCCESSFUL
                return True


def take_existing_registration_off_waiting_list(dao: TicketsDAO, registration: ProductRegistration,
                                                new_partner: PersonInfo=None):
    if (registration.paid_price or 0) < registration.price:
        payment = dao.get_payment_by_registration(registration)
        price = registration.price - (registration.paid_price or 0)
        fee = transaction_fee(price)
        if stripe_charge_customer(payment, config.STRIPE_SK, price + fee):
            registration.paid_price = price
            dao.update_payment(payment)
        else:
            # TODO: better notification
            print('EXTRA PAYMENT FAILED')

    if new_partner is not None:
        registration.partner = new_partner
    registration.wait_listed = False
    dao.update_registration(registration)
    send_waiting_list_accept_email(dao, registration)


def do_get_payment_status(dao: TicketsDAO):
    form = StripeCheckoutForm()
    if form.validate_on_submit():
        payment = dao.get_payment_by_id(form.payment_id.data)
        if payment.stripe is None or payment.stripe.token_id is None:
            return PaymentResult(success=False, complete=False, error_message='Payment not initiated yet')
        elif payment.stripe.token_id == form.stripe_token.data['id']:
            return PaymentResult.from_paid_payment(payment)

    print(form.errors)
    return PaymentResult(success=False, error_message='Access denied to see payment status')


def balance_event_waiting_lists(dao: TicketsDAO, event: Event):
    balanced_registrations = []
    event = dao.get_event_by_key(event.key)
    for product_key, product in event.products.items():
        if isinstance(product, WaitListedPartnerProduct):
            if product.waiting_list.has_waiting_list:
                for registration in product.balance_waiting_list():
                    take_existing_registration_off_waiting_list(dao, registration)
                    balanced_registrations.append(registration)


def registration_post_process(dao: TicketsDAO, payment: Payment):
    """send emails, balance waiting lists"""
    event = dao.get_payment_event(payment)
    send_registration_confirmation(payment, event)
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


# def get_pay_now(payment: Payment) -> float:
#     accepted_prices = [r.price for r in payment.registrations if not r.wait_listed]
#     return sum(accepted_prices)
#
#
# def get_later_pay_amounts(payment: Payment) -> List[float]:
#     return [r.price for r in payment.registrations if r.wait_listed]


def set_payment_totals(payment: Payment):
    payment.price = sum([r.price for r in payment.registrations if r.price] or [0])
    if payment.pay_all_now:
        payment.transaction_fee = transaction_fee(payment.price)
        payment.first_pay_amount = payment.price
    else:
        accepted_prices = [r.price for r in payment.registrations if not r.wait_listed and r.price]
        payment.first_pay_amount = sum(accepted_prices or [0])

        # here we calculate sum of transaction fees for first payment and all waiting separately
        wait_listed_prices = [r.price for r in payment.registrations if r.wait_listed and r.price]
        all_payments = [payment.first_pay_amount] + wait_listed_prices
        payment.transaction_fee = transaction_fee(*all_payments)

    payment.first_pay_fee = transaction_fee(payment.first_pay_amount)
