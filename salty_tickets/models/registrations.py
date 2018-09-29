from datetime import datetime
from typing import List, Dict

from dataclasses import dataclass, field
from salty_tickets.constants import NEW, SUCCESSFUL, ACCEPTED


@dataclass(unsafe_hash=True)
class PersonInfo:
    full_name: str
    email: str
    location: Dict = field(default_factory=dict, hash=False)
    comment: str = None


@dataclass
class ProductRegistration:
    registered_by: PersonInfo = None
    person: PersonInfo = None
    partner: PersonInfo = None
    dance_role: str = None
    wait_listed: bool = False
    details: Dict = field(default_factory=dict)
    price: float = None
    paid_price: float = None
    paid: float = None
    date: datetime = None
    product_key: str = None
    active: bool = False

    @property
    def as_couple(self):
        return bool(self.partner)


@dataclass
class PaymentStripeDetails:
    token_id: str = None
    customer_id: str = None
    charges: List = field(default_factory=list)
    error_response: Dict = field(default_factory=dict)


@dataclass
class Payment:
    paid_by: PersonInfo
    price: float = 0
    description: str = ''
    transaction_fee: float = 0
    registrations: List[ProductRegistration] = field(default_factory=list)

    status: str = NEW
    stripe: PaymentStripeDetails = None
    date: datetime = field(default_factory=datetime.utcnow)
    info_items: List = field(default_factory=list)
    extra_registrations: List[ProductRegistration] = field(default_factory=list)

    pay_all_now: bool = True
    first_pay_amount: float = 0
    first_pay_fee: float = 0

    def __post_init__(self):
        if self.price and self.pay_all_now and not self.first_pay_amount:
            self.first_pay_amount = self.price
            self.first_pay_fee = self.transaction_fee

    @property
    def total_amount(self):
        if self.price > 0:
            return self.price + self.transaction_fee
        else:
            return 0

    @property
    def first_pay_total(self):
        if self.first_pay_amount > 0:
            return self.first_pay_amount + self.first_pay_fee
        else:
            return 0

    @property
    def paid_price(self):
        return sum([r.paid_price or 0 for r in self.registrations] or [0])
