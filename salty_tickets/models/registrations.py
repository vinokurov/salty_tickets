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
    paid: float = None
    date: datetime = None
    product_key: str = None
    active: bool = False

    @property
    def as_couple(self):
        return bool(self.partner)


@dataclass
class PaymentStripeDetails:
    source: Dict = field(default_factory=dict)
    charge_id: str = None
    charge: Dict = field(default_factory=dict)


@dataclass
class Payment:
    price: float
    paid_by: PersonInfo
    description: str = ''
    transaction_fee: float = 0
    registrations: List[ProductRegistration] = field(default_factory=list)

    status: str = NEW
    stripe: PaymentStripeDetails = None
    date: datetime = field(default_factory=datetime.utcnow)
    info_items: List = field(default_factory=list)
    extra_registrations: List[ProductRegistration] = field(default_factory=list)

    @property
    def total_amount(self):
        if self.price > 0:
            return self.price + self.transaction_fee
        else:
            return 0
