from typing import Dict, List

from dataclasses import dataclass, field
from dataclasses_json import DataClassJsonMixin
from salty_tickets.constants import NEW
from salty_tickets.dao import TicketsDAO
from salty_tickets.forms import get_primary_personal_info_from_form, get_partner_personal_info_from_form
from salty_tickets.models.event import Event
from salty_tickets.models.registrations import Payment
from salty_tickets.payments import transaction_fee
from salty_tickets.pricers import ProductPricer

"""
Before chackout:
    - get form data
    - price products, validate fields
    - return JSON with prices, field validation, etc

Checkout:
    - generate Payment instance (with prices)
    - save with status new
    - return stripe details
"""


@dataclass
class OrderSummary(DataClassJsonMixin):
    total: float = 0
    items: List[str] = field(default_factory=list)


@dataclass
class PricingResult(DataClassJsonMixin):
    """These are AJAX objects containing result of pricing"""
    errors: Dict[str, str] = field(default_factory=dict)
    stripe: Dict = field(default_factory=dict)
    order_summary: OrderSummary = field(default_factory=OrderSummary)
    disable_checkout: bool = True
    checkout_success: bool = False


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
        stripe_details={},
        info_items=[r.info for r in registrations]
    )
    return payment


def checkout_payment(event: Event, new_payment: Payment):
    pass

def registration_payment_success(event, registration, payment_details):
    pass


def registration_payment_failed(event, registration, payment_details):
    pass
