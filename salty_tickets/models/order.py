from datetime import datetime

from dataclasses import dataclass, field


@dataclass
class Order:
    full_name: str
    email: str
    total_price: float = 0
    total_paid: float = 0
    purchases: list = field(default_factory=list)
    payments: list = field(default_factory=list)

    def update_total_price(self):
        self.total_price = sum([i.price for i in self.purchase_items])

    def update_total_paid(self):
        self.total_paid = sum([p.price for p in self.payments if p.status == 'success'])


@dataclass
class Purchase:
    date: datetime = field(default_factory=datetime.utcnow)
    purchase_items: list = field(default_factory=list)
    total_price: float = 0

    def update_total_price(self):
        self.total_price = sum([i.price for i in self.purchase_items])


@dataclass
class PurchaseItem:
    name: str
    product_key: str
    parameters: dict = field(default_factory=dict)
    price: float = None


@dataclass
class Payment:
    price: float
    transaction_fee: float = 0
    total_amount: float = 0

    status: str = 'new'
    stripe_details: dict = field(default_factory=dict)
    date: datetime = field(default_factory=datetime.utcnow)

