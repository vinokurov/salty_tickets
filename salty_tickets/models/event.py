from datetime import datetime
from typing import Dict

from dataclasses import dataclass, field
from salty_tickets.utils import string_to_key


@dataclass
class Event:
    name: str
    key: str = None
    start_date: datetime = None
    end_date: datetime = None
    info: str = None
    active: bool = False
    products: Dict = field(default_factory=dict)
    pricing_rules: Dict = field(default_factory=dict)

    def __post_init__(self):
        if self.key is None:
            self.key = string_to_key(self.name)

    def append_products(self, product_list):
        self.products.update({p.key: p for p in product_list})

