from datetime import datetime
from typing import List, Dict

from dataclasses import dataclass, field
from salty_tickets.constants import NEW, SUCCESSFUL


@dataclass
class PersonInfo:
    full_name: str
    email: str
    location: Dict = field(default_factory=dict)
    comment: str = None


@dataclass
class ProductRegistration:
    registered_by: PersonInfo = None
    person: PersonInfo = None
    partner: PersonInfo = None
    dance_role: str = None
    as_couple: bool = False
    status: str = None
    details: Dict = field(default_factory=dict)
    price: float = None
    paid: float = None
    date: datetime = None
    product_key: str = None

    def __post_init__(self):
        if self.partner:
            self.as_couple = True


@dataclass
class Payment:
    price: float
    paid_by: PersonInfo
    transaction_fee: float = 0
    registrations: List[ProductRegistration] = field(default_factory=list)

    status: str = NEW
    stripe_details: Dict = field(default_factory=dict)
    date: datetime = field(default_factory=datetime.utcnow)
    info_items: List = field(default_factory=list)

    @property
    def total_amount(self):
        return self.price + self.transaction_fee
