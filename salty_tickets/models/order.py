from datetime import datetime
from typing import List, Dict

from dataclasses import dataclass, field
from salty_tickets.constants import NEW, SUCCESSFUL


@dataclass
class PurchaseItem:
    name: str
    product_key: str
    parameters: Dict = field(default_factory=dict)
    price: float = None


@dataclass
class Purchase:
    date: datetime = field(default_factory=datetime.utcnow)
    items: List[PurchaseItem] = field(default_factory=list)
    total_price: float = 0

    def __post_init__(self):
        self.update_total_price()

    def update_total_price(self):
        self.total_price = sum([i.price for i in self.items if i.price is not None])


@dataclass
class Payment:
    price: float
    transaction_fee: float = 0
    total_amount: float = 0

    status: str = NEW
    stripe_details: dict = field(default_factory=dict)
    date: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Order:
    full_name: str
    email: str
    total_price: float = 0
    total_paid: float = 0
    purchases: List[Purchase] = field(default_factory=list)
    payments: List[Payment] = field(default_factory=list)

    def __post_init__(self):
        self.update_total_price()
        self.update_total_paid()

    def update_total_price(self):
        for p in self.purchases:
            p.update_total_price()
        self.total_price = sum([p.total_price for p in self.purchases if p.total_price is not None])

    def update_total_paid(self):
        self.total_paid = sum([p.price for p in self.payments if p.status == SUCCESSFUL])


