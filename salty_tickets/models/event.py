from datetime import datetime

from dataclasses import dataclass, field
from salty_tickets.utils import string_to_key


@dataclass
class Event:
    name: str
    key: str
    start_date: datetime
    end_date: datetime
    info: str = None
    active: bool = False
    products: dict = field(default_factory=dict)
    pricing_rules: dict = field(default_factory=dict)

    def __post_init__(self):
        self.key = string_to_key(self.name)

    def append_products(self, product_list):
        self.products.update({p.key: p for p in product_list})

