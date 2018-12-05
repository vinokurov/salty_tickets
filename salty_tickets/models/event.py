from datetime import datetime
from typing import Dict, List

from dataclasses import dataclass, field
from salty_tickets.models.products import Product
from salty_tickets.models.tickets import Ticket
from salty_tickets.utils.utils import string_to_key


@dataclass
class Event:
    name: str
    key: str = None
    start_date: datetime = None
    end_date: datetime = None
    info: str = None
    active: bool = False
    tickets: Dict[str, Ticket] = field(default_factory=dict)
    products: Dict[str, Product] = field(default_factory=dict)
    pricing_rules: List = field(default_factory=list)
    validation_rules: List = field(default_factory=list)
    layout: Dict = None

    def __post_init__(self):
        if self.key is None:
            self.key = string_to_key(self.name)

    def append_tickets(self, ticket_list):
        self.tickets.update({p.key: p for p in ticket_list})
