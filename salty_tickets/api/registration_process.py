import pickle
import typing
from typing import Dict, List, Optional

from dataclasses import dataclass, field
from dataclasses_json import DataClassJsonMixin
from flask import session
from itsdangerous import BadSignature
from salty_tickets import config
from salty_tickets.constants import NEW, SUCCESSFUL, FAILED, LEADER, FOLLOWER, COUPLE
from salty_tickets.dao import TicketsDAO
from salty_tickets.emails import send_waiting_list_accept_email, send_registration_confirmation
from salty_tickets.forms import create_event_form, StripeCheckoutForm, DanceSignupForm, PartnerTokenCheck, \
    CreateRegistrationGroupForm, \
    add_primary_person_to_form_cache, add_partner_person_to_form_cache
from salty_tickets.models.discounts import CodeDiscountProduct, DiscountProduct, get_discount_rule_from_code, \
    GroupDiscountProduct
from salty_tickets.models.event import Event
from salty_tickets.models.products import Product
from salty_tickets.models.registrations import Payment, Person, PaymentStripeDetails, Registration, RegistrationGroup, \
    TransactionDetails
from salty_tickets.models.tickets import WaitListedPartnerTicket, WorkshopTicket, Ticket, PartyTicket, \
    FestivalPassTicket
from salty_tickets.payments import transaction_fee, stripe_charge, stripe_create_customer, stripe_charge_customer
from salty_tickets.pricers import TicketPricer
from salty_tickets.tokens import PartnerToken, PaymentId, DiscountToken, GroupToken, RegistrationToken
from salty_tickets.validators import validate_registrations

"""
Before checkout:
    - get form data
    - price tickets, validate fields
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
class TicketWaitingListInfo(DataClassJsonMixin):
    leader: Optional[int] = None
    follower: Optional[int] = None
    couple: Optional[int] = None


@dataclass
class TicketInfo(DataClassJsonMixin):
    key: str
    title: str
    start_datetime: str = None
    end_datetime: str = None
    time: str = None
    level: str = None
    teachers: str = None
    location: str = None
    available: int = None
    editable: bool = True
    price: float = None
    info: str = None
    choice: str = None
    tags: List = field(default_factory=[])
    waiting_list: Optional[TicketWaitingListInfo] = None

    @classmethod
    def from_workshop(cls, ticket: Ticket):
        ticket_info = cls(
            key=ticket.key,
            title=ticket.name,
            available=100,
            # available=ticket.get_available_quantity(),
            price=ticket.base_price,
            info=ticket.info,
            tags=list(ticket.tags)
        )
        if hasattr(ticket, 'start_datetime'):
            ticket_info.start_datetime = str(ticket.start_datetime)

        if hasattr(ticket, 'end_datetime'):
            ticket_info.end_datetime = str(ticket.end_datetime)

        if hasattr(ticket, 'location'):
            ticket_info.location = ticket.location

        if isinstance(ticket, PartyTicket):
            available = ticket.max_available - ticket.waiting_list.total_accepted
            ticket_info.available = available

        if isinstance(ticket, WorkshopTicket):
            available = ticket.max_available - ticket.waiting_list.total_accepted
            waiting_stats = ticket.waiting_list.waiting_stats
            ticket_info.waiting_list = TicketWaitingListInfo(
                leader=int(waiting_stats[LEADER] * 100) if waiting_stats[LEADER] is not None else None,
                follower=int(waiting_stats[FOLLOWER] * 100) if waiting_stats[FOLLOWER] is not None else None,
                couple=int(waiting_stats[COUPLE] * 100) if waiting_stats[COUPLE] is not None else None,
            )
            ticket_info.available = available
            ticket_info.level = ticket.level
            ticket_info.teachers = ticket.teachers
        return ticket_info


@dataclass
class ProductInfo(DataClassJsonMixin):
    key: str
    title: str
    options: Dict
    available: int = None
    price: float = None
    info: str = None
    choice: Dict = field(default_factory=dict)
    image_urls: List = field(default_factory=list)

    @classmethod
    def from_product(cls, product: Product):
        return cls(
            title=product.name,
            key=product.key,
            options=product.options,
            price=product.base_price,
            info=product.info,
            available=100,
            image_urls=product.image_urls,
        )


# @dataclass
# class DiscountProductInfo(DataClassJsonMixin):
#     key: str
#     title: str
#     options: Dict
#     available: int = None
#     price: float = None
#     info: str = None
#     choice: str = None


@dataclass
class EventRegistrationStatsInfo(DataClassJsonMixin):
    persons_count: int = None
    workshops_accepted: int = None
    countries_count: int = None
    locations_count: int = None

    @classmethod
    def from_event(cls, event: Event):
        registrations = []
        for p_key, p in event.tickets.items():
            registrations = registrations + p.registrations
        registrations = [r for r in registrations if r.active]
        persons = {r.person.full_name.lower(): r.person for r in registrations}.values()

        def location_to_tuple(location_dict):
            return tuple({k: v for k, v in location_dict.items() if k != 'query'}.items())

        return cls(
            persons_count=len(persons),
            workshops_accepted=len([r for r in registrations if not r.wait_listed
                                    and isinstance(event.tickets[r.ticket_key], WorkshopTicket)]),
            countries_count=len(set([p.location.get('country_code') for p in persons])),
            locations_count=len(set([location_to_tuple(p.location) for p in persons])),
        )


@dataclass
class EventInfo(DataClassJsonMixin):
    name: str
    key: str
    active: bool
    tickets: List
    products: List
    # discount_products: List
    layout: Dict
    registrations_stats: EventRegistrationStatsInfo = None

    @classmethod
    def from_event(cls, event):

        return cls(
            name=event.name,
            key=event.key,
            active=event.active,
            tickets=[TicketInfo.from_workshop(p) for k, p in event.tickets.items()],
            products=[ProductInfo.from_product(p) for k, p in event.products.items()],
            # discount_products=[DiscountProductInfo.from_discount_product(p)
            #                    for k, p in event.discount_products.items()],
            layout=event.layout,
            registrations_stats=EventRegistrationStatsInfo.from_event(event),
        )


@dataclass
class OrderItem(DataClassJsonMixin):
    name: str
    price: float
    key: str
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
                name=event.tickets[reg.ticket_key].name,
                key=reg.ticket_key,
                price=reg.price,
                person=reg.person.full_name,
                partner=reg.partner.full_name if reg.partner else None,
                dance_role=reg.dance_role,
                wait_listed=reg.wait_listed
            ))
        for purchase in payment.purchases:
            name = event.products[purchase.product_key].name
            option_name = event.products[purchase.product_key].options[purchase.product_option_key]
            amount = purchase.amount
            name = f'{name} / {option_name} / {amount}'
            items.append(OrderItem(
                name=name,
                price=purchase.price,
                key=purchase.product_key,
            ))
        for discount in payment.discounts:
            items.append(OrderItem(
                name=discount.description,
                price=-discount.value,
                key=''
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
    # new_prices: Dict = field(default_factory=dict)
    new_prices: typing.List = field(default_factory=list)

    @classmethod
    def from_payment(cls, event: Event, payment: Payment, errors: Dict, new_prices=None):
        obj = cls(
            stripe=StripeData.from_payment(payment),
            order_summary=OrderSummary.from_payment(event, payment),
            errors=errors,
        )
        if new_prices is not None:
            obj.new_prices = new_prices
        return obj

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
                   roles={r.ticket_key: r.dance_role for r in active_registrations})


def get_payment_from_form(event: Event, form, extra_registrations=None,
                          prior_registrations=None, discount_product: DiscountProduct=None):
    registrations = []
    for ticket_key, ticket in event.tickets.items():
        registrations += ticket.parse_form(form)

    validate_registrations(event, registrations + (prior_registrations or []))

    purchases = []
    for product_key, product in event.products.items():
        purchases += product.parse_form(form)

    # apply extra registrations
    if extra_registrations is not None:
        applied_extra_registrations = []
        for reg in [r for r in registrations if not r.partner]:
            ticket = event.tickets[reg.ticket_key]
            if isinstance(ticket, WaitListedPartnerTicket):
                applied_reg = ticket.apply_extra_partner(reg, extra_registrations)
                if applied_reg:
                    applied_extra_registrations.append(applied_reg)
    else:
        applied_extra_registrations = None

    # add prices
    pricer = TicketPricer.from_event(event)
    pricer.price_all(registrations, prior_registrations=prior_registrations)

    if len(registrations):
        person = registrations[0].registered_by
    elif len(purchases):
        person = purchases[0].person
    else:
        person = None # ??? ACTUALLY CHECK

    payment = Payment(
        paid_by=person,
        registrations=registrations,
        purchases=purchases,
        status=NEW,
        info_items=[(event.tickets[r.ticket_key].item_info(r), r.price) for r in registrations],
        pay_all_now=form.pay_all.data,
    )

    if discount_product:
        payment.discounts = discount_product.get_discount(event.tickets, payment, form)

    set_payment_totals(payment)

    if applied_extra_registrations is not None:
        payment.extra_registrations = applied_extra_registrations

    return payment


def get_discount_product_from_form(dao: TicketsDAO, event: Event, form):
    discount_code = form.generic_discount_code.data
    if discount_code:
        discount_code = discount_code.strip()
        if discount_code == 'OVERSEAS':
            form.get_item_by_key('overseas_discount').validated.data = 'yes'
        elif discount_code.startswith('grp_'):
            form.get_item_by_key('group_discount').validated.data = 'yes'
            form.get_item_by_key('group_discount').code.data = discount_code
        elif discount_code.startswith('dsc_'):
            form.get_item_by_key('discount_code').validated.data = 'yes'
            form.get_item_by_key('discount_code').code.data = discount_code

    for discount_product_key, discount_product in event.discount_products.items():
        if discount_product.is_added(form):
            if isinstance(discount_product, CodeDiscountProduct):
                discount_form = form.get_item_by_key(discount_product.key)
                token_str = discount_form.code.data
                discount_code = DiscountToken().deserialize(dao, token_str)
                if discount_code.can_be_used:
                    discount_rule = get_discount_rule_from_code(discount_code)
                    print(discount_rule)
                    return CodeDiscountProduct(
                        name=discount_product.name,
                        discount_rule=discount_rule,
                        applies_to_couple=discount_code.applies_to_couple,
                        discount_code=discount_code,
                    )
            else:
                return discount_product


def get_extra_registrations_from_partner_token(dao: TicketsDAO, event: Event, form):
    if form.partner_token.data:
        partner = PartnerToken().deserialize(dao, form.partner_token.data)
        return dao.query_registrations(event, partner)


def try_resolve_person_tokens_in_form(form: DanceSignupForm, dao: TicketsDAO) -> Person:
    if form.partner_registration_token.data:
        try:
            partner_person = RegistrationToken().deserialize(dao, form.partner_registration_token.data.strip())
            if partner_person is not None:
                form.partner_name.data = partner_person.full_name
                form.partner_email.data = partner_person.email
                form.partner_location.data = partner_person.location
                add_partner_person_to_form_cache(form, partner_person)
        except BadSignature:
            pass
    if form.registration_token.data:
        try:
            primary_person = RegistrationToken().deserialize(dao, form.registration_token.data.strip())
            if primary_person is not None:
                form.name.data = primary_person.full_name
                form.email.data = primary_person.email
                form.location.data = primary_person.location
                add_primary_person_to_form_cache(form, primary_person)
                return primary_person
        except BadSignature:
            pass


def do_price(dao: TicketsDAO, event_key: str):
    event = dao.get_event_by_key(event_key)
    form = create_event_form(event)()
    prior_registred_by = try_resolve_person_tokens_in_form(form, dao)
    valid = form.validate_on_submit()

    prior_registrations = get_prior_registrations(dao, event, prior_registred_by)
    extra_registrations = get_extra_registrations_from_partner_token(dao, event, form)
    discount_product = get_discount_product_from_form(dao, event, form)

    payment = get_payment_from_form(event, form, extra_registrations=extra_registrations,
                                    prior_registrations=prior_registrations,
                                    discount_product=discount_product)
    if payment:
        errors = {}
        errors.update(validate_registrations(event, payment.registrations + prior_registrations))
        errors.update(form.errors)
        new_prices = get_new_prices(event, payment.paid_by or prior_registred_by,
                                    payment.registrations + prior_registrations)
        return PricingResult.from_payment(event, payment, errors, new_prices=new_prices)


def get_prior_registrations(dao: TicketsDAO, event: Event, prior_registred_by):
    if prior_registred_by is not None:
        prior_registrations = dao.query_registrations(event, registered_by=prior_registred_by)
        prior_registrations = [r for r in prior_registrations if r.active]
    else:
        prior_registrations = []
    return prior_registrations


def do_checkout(dao: TicketsDAO, event_key: str):
    event = dao.get_event_by_key(event_key)
    form = create_event_form(event)()
    prior_registred_by = try_resolve_person_tokens_in_form(form, dao)
    valid = form.validate_on_submit()

    prior_registrations = get_prior_registrations(dao, event, prior_registred_by)
    extra_registrations = get_extra_registrations_from_partner_token(dao, event, form)
    discount_product = get_discount_product_from_form(dao, event, form)

    payment = get_payment_from_form(event, form, extra_registrations=extra_registrations,
                                    prior_registrations=prior_registrations,
                                    discount_product=discount_product)

    if payment:
        errors = {}
        errors.update(validate_registrations(event, payment.registrations + prior_registrations))
        errors.update(form.errors)
        new_prices = get_new_prices(event, payment.paid_by or prior_registred_by,
                                    payment.registrations + prior_registrations)
        pricing_result = PricingResult.from_payment(event, payment, errors, new_prices=new_prices)
        if valid and not errors and not pricing_result.disable_checkout:
            session['payment'] = pickle.dumps(payment)
            session['event_key'] = event_key
            pricing_result.checkout_success = not pricing_result.disable_checkout
        return pricing_result


def do_pay(dao: TicketsDAO):
    form = StripeCheckoutForm()
    valid = form.validate_on_submit()
    if not valid:
        error_message = 'API error. Please check your registration details.'
        return PaymentResult(success=False, complete=True, error_message=error_message)

    payment_pickle = session.get('payment', None)
    if not payment_pickle:
        error_message = 'Payment information has expired. Please try again.'
        return PaymentResult(success=False, complete=True, error_message=error_message)

    payment = pickle.loads(payment_pickle)

    event_key = session.get('event_key', None)
    if not event_key:
        error_message = 'API error. Please check your registration details.'
        return PaymentResult(success=False, complete=True, error_message=error_message)

    if payment is None or payment.status not in [NEW, FAILED]:
        error_message = 'Payment information has expired. Please try again.'
        return PaymentResult(success=False, error_message=error_message)

    event = dao.get_event_by_key(event_key, get_registrations=False)
    payment.description = event.name
    stripe_token_id = form.stripe_token.data.get('id')
    payment.stripe = PaymentStripeDetails(token_id=stripe_token_id)

    if hasattr(payment, 'id') and payment.id:
        dao.update_payment(payment)
    else:
        dao.add_payment(payment, event, register=True)

    # if payment.price == 0:
    #     success = True
    #     payment.status = SUCCESSFUL
    # else:
    success = process_first_payment(payment)
    dao.update_payment(payment)
    session['payment'] = pickle.dumps(payment)

    if not success:
        error_message = 'Payment has been declined by the provider.'
        try:
            error_message = error_message + ' ' + payment.stripe.error_response['error']['message']
        except Exception as err:
            pass
        return PaymentResult(success=False, complete=True,
                             error_message=error_message, payment_id=str(payment.id))

    session.pop('payment')
    session.pop('event_key')
    for reg in payment.registrations:
        reg.active = True
        dao.update_registration(reg)

    for purchase in payment.purchases:
        purchase.active = True
        dao.update_purchase(purchase)

    # TODO: make it nicer - with emails, etc.
    if payment.extra_registrations:
        for reg in payment.registrations:
            for extra_reg in payment.extra_registrations:
                if extra_reg.active and (reg.ticket_key == extra_reg.ticket_key):
                    take_existing_registration_off_waiting_list(dao, extra_reg, reg.registered_by)

    # these are optional things. if they get failed, registration is still successfull
    try:
        registration_post_process(dao, payment)
    except Exception as e:
        print(e)

    return PaymentResult.from_paid_payment(payment)


def process_first_payment(payment: Payment):
    if payment.price and (payment.pay_all_now or (payment.first_pay_amount == payment.price)):
        transaction = TransactionDetails(
            price=payment.price,
            transaction_fee=payment.transaction_fee,
            description='Card payment'
        )
        if stripe_charge(transaction, payment, config.STRIPE_SK):
            # update paid prices on all registrations
            for item in payment.items:
                item.is_paid = True
            return True
    else:
        if stripe_create_customer(payment, config.STRIPE_SK):
            if payment.first_pay_amount > 0:
                transaction = TransactionDetails(
                    price=payment.first_pay_amount,
                    transaction_fee=payment.first_pay_fee,
                    description='Card payment'
                )
                if stripe_charge_customer(transaction, payment, config.STRIPE_SK):
                    # update paid prices on accepted registrations
                    for item in payment.items:
                        if not (hasattr(item, 'wait_listed') and item.wait_listed):
                            item.is_paid = True
                    return True
            else:
                payment.status = SUCCESSFUL
                return True


def take_existing_registration_off_waiting_list(dao: TicketsDAO, registration: Registration,
                                                new_partner: Person=None):
    if not registration.is_paid:
        payment = dao.get_payment_by_registration(registration)
        transaction = TransactionDetails(
            price=registration.price,
            transaction_fee=transaction_fee(registration.price),
            description='Automatic payment'
        )
        if stripe_charge_customer(transaction, payment, config.STRIPE_SK):
            # registration.paid_price = price
            registration.is_paid = True
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


def balance_event_waiting_lists(dao: TicketsDAO, event_key: str):
    balanced_registrations = []

    # it is a good idea to refresh event object
    event = dao.get_event_by_key(event_key)
    for ticket_key, ticket in event.tickets.items():
        if isinstance(ticket, WaitListedPartnerTicket):
            if ticket.waiting_list.has_waiting_list:
                for registration in ticket.balance_waiting_list():
                    take_existing_registration_off_waiting_list(dao, registration)
                    balanced_registrations.append(registration)


def post_process_discounts(dao: TicketsDAO, payment: Payment, event: Event):
    for discount in payment.discounts:
        discount_product = event.discount_products[discount.discount_key]

        # GroupDiscount -> add new members to the group
        if isinstance(discount_product, GroupDiscountProduct):
            registration_group = GroupToken().deserialize(dao, discount.discount_code)
            dao.add_registration_group_member(registration_group, discount.person)

        # Code discount -> increment code usages
        elif isinstance(discount_product, CodeDiscountProduct):
            discount_code = DiscountToken().deserialize(dao, discount.discount_code)
            dao.increment_discount_code_usages(discount_code, 1)


def registration_post_process(dao: TicketsDAO, payment: Payment):
    """send emails, balance waiting lists"""
    event = dao.get_payment_event(payment)
    post_process_discounts(dao, payment, event)
    send_registration_confirmation(payment, event)
    balance_event_waiting_lists(dao, event.key)


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
    payment.price = max(0, sum([r.price for r in payment.items if r.price] or [0]))
    discounts_value = sum([d.value for d in payment.discounts if d.value] or [0])
    if discounts_value:
        if discounts_value > payment.price:
            payment.price = 0
        else:
            payment.price -= discounts_value
        payment.pay_all_now = True

    if payment.pay_all_now:
        payment.transaction_fee = transaction_fee(payment.price)
        payment.first_pay_amount = payment.price
    else:
        accepted_prices = [r.price for r in payment.registrations if not r.wait_listed and r.price]
        accepted_prices += [p.price for p in payment.purchases if p.price]
        payment.first_pay_amount = sum(accepted_prices or [0])

        # here we calculate sum of transaction fees for first payment and all waiting separately
        wait_listed_prices = [r.price for r in payment.registrations if r.wait_listed and r.price]
        all_payments = [payment.first_pay_amount] + wait_listed_prices
        payment.transaction_fee = transaction_fee(*all_payments)

    payment.first_pay_fee = transaction_fee(payment.first_pay_amount)


@dataclass
class CreateRegistrationGroupResult(DataClassJsonMixin):
    success: bool = False
    errors: typing.Dict = field(default_factory=dict)
    token: str = None


@dataclass
class TokenCheckResult(DataClassJsonMixin):
    success: bool = False
    info: str = None


def do_create_registration_group(dao: TicketsDAO, event_key: str):
    event = dao.get_event_by_key(event_key, get_registrations=False)
    form = CreateRegistrationGroupForm()
    errors = {}
    if form.validate_on_submit():
        name = form.name.data.strip()
        if dao.check_registration_group_name_exists(event, name):
            errors.update({'name': 'Group name already exists'})
        else:
            registration_group = RegistrationGroup(
                name=name,
                location=form.location.data,
                admin_email=form.email.data,
                comment=form.comment.data,
            )
            dao.add_registration_group(event, registration_group)
            token_str = GroupToken().serialize(registration_group)
            return CreateRegistrationGroupResult(success=True, token=token_str)
    errors.update(form.errors)
    return CreateRegistrationGroupResult(errors=errors)


@dataclass
class DiscountCodeTokenCheckResult(TokenCheckResult):
    included_tickets: typing.List = field(default_factory=list)
    name_override: str = None
    email_override: str = None


def do_validate_registration_group_token(dao: TicketsDAO, event_key: str) -> TokenCheckResult:
    event = dao.get_event_by_key(event_key, get_registrations=False)
    form = create_event_form(event)()
    valid = form.validate_on_submit()
    if form.location.data is not None:
        group_discount_form = form.get_item_by_key('group_discount')
        if group_discount_form is not None:
            token_str = group_discount_form.code.data
            try:
                registration_group = GroupToken().deserialize(dao, token_str)
            except BadSignature:
                return TokenCheckResult(success=False)
            if registration_group:
                if registration_group.location['country_code'] == form.location.data['country_code']:
                    return TokenCheckResult(success=True, info=registration_group.name)

    return TokenCheckResult(success=False)


def do_validate_discount_code_token(dao: TicketsDAO, event_key: str) -> TokenCheckResult:
    event = dao.get_event_by_key(event_key, get_registrations=False)
    form = create_event_form(event)()
    valid = form.validate_on_submit()
    discount_product = [d for k, d in event.discount_products.items() if isinstance(d, CodeDiscountProduct)][0]
    discount_form = form.get_item_by_key(discount_product.key)
    token_str = discount_form.code.data
    try:
        discount_code = DiscountToken().deserialize(dao, token_str)
    except BadSignature:
        return TokenCheckResult(success=False)
    if discount_code.can_be_used:
        return DiscountCodeTokenCheckResult(
            success=True,
            info=discount_code.info,
            name_override=discount_code.full_name,
            email_override=discount_code.email,
            included_tickets=discount_code.included_tickets
        )

    return TokenCheckResult(success=False)


@dataclass
class RegistrationInfo(DataClassJsonMixin):
    ticket_key: str
    person: str
    price: float

    @classmethod
    def from_registration(cls, registration: Registration):
        return cls(
            ticket_key=registration.ticket_key,
            person=registration.person.full_name,
            price=registration.price
        )


@dataclass
class PriorRegistrationsInfo(DataClassJsonMixin):
    person: str = None
    partner: str = None
    partner_reg_token: str = None
    registrations: typing.List[RegistrationInfo] = field(default_factory=list)
    new_prices: typing.List = field(default_factory=list)
    dance_role: str = None

    @classmethod
    def from_registration_list(cls, registrations: typing.List[Registration], person: Person):
        regs_info = cls(person=person.full_name)
        if registrations:
            regs_info.registrations = [RegistrationInfo.from_registration(r) for r in registrations]
            for reg in registrations:
                if reg.person != person:
                    regs_info.partner = reg.person.full_name
                    regs_info.partner_reg_token = RegistrationToken().serialize(reg.person)
                    break
        return regs_info


def do_get_prior_registrations(dao: TicketsDAO, event_key: str) -> PriorRegistrationsInfo:
    event = dao.get_event_by_key(event_key, get_registrations=False)
    form = create_event_form(event)()
    valid = form.validate_on_submit()

    person = try_resolve_person_tokens_in_form(form, dao)
    if person:
        registrations = get_prior_registrations(dao, event, person)
        regs_info = PriorRegistrationsInfo.from_registration_list(registrations, person)
        regs_info.new_prices = get_new_prices(event, person, registrations)

        for reg in registrations:
            if reg.person == person and reg.dance_role in [LEADER, FOLLOWER]:
                regs_info.dance_role = reg.dance_role
                break

        return regs_info

    return PriorRegistrationsInfo()


def get_new_prices(event: Event, person: Person, registrations: typing.List[Registration]):
    pricer = TicketPricer.from_event(event)
    new_prices = []
    for ticket_key, ticket in event.tickets.items():
        if ticket_key not in [r.ticket_key for r in registrations]:
            ticket_reg = Registration(
                registered_by=person,
                person=person,
                ticket_key=ticket_key
            )
            pricer.price_all([ticket_reg], prior_registrations=registrations)
            new_prices.append({'ticket_key': ticket_key, 'price': ticket_reg.price})
    return new_prices



