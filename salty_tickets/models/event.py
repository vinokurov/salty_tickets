import itertools
from datetime import datetime
from typing import Dict, List

from dataclasses import dataclass, field

import typing

from dataclasses_json import DataClassJsonMixin
from salty_tickets.models.discounts import DiscountProduct
from salty_tickets.models.products import Product
from salty_tickets.models.registrations import Registration
from salty_tickets.models.tickets import Ticket, WorkshopTicket
from salty_tickets.utils.utils import string_to_key


@dataclass
class EventSummaryNumbers(DataClassJsonMixin):
    persons_count: int = None
    workshops_accepted: int = None
    countries_count: int = None
    locations_count: int = None

    @classmethod
    def from_event(cls, event):
        return cls()

    # TODO: unit tests


@dataclass
class Event:
    name: str
    key: typing.Optional[str] = None
    start_date: datetime = None
    end_date: datetime = None
    info: str = None
    active: bool = False
    tickets: Dict[str, Ticket] = field(default_factory=dict)
    products: Dict[str, Product] = field(default_factory=dict)
    discount_products: Dict[str, DiscountProduct] = field(default_factory=dict)
    pricing_rules: List = field(default_factory=list)
    validation_rules: List = field(default_factory=list)
    layout: Dict = None
    summary_numbers: EventSummaryNumbers = field(default_factory=EventSummaryNumbers)

    id = None

    def __post_init__(self):
        if self.key is None:
            self.key = string_to_key(self.name)

    def append_tickets(self, ticket_list: List[Ticket]):
        self.tickets.update({p.key: p for p in ticket_list})

    def append_products(self, product_list: List[Product]):
        self.products.update({p.key: p for p in product_list})

    def append_discount_products(self, discount_product_list: List[DiscountProduct]):
        self.discount_products.update({p.key: p for p in discount_product_list})

    def calculate_registration_numbers(self, ticket_registrations: List[Registration]):
        registrations = list(itertools.chain(*list(ticket_registrations.values())))
        registrations = [r for r in registrations if r.active]
        persons = {r.person.full_name.lower(): r.person for r in registrations}.values()

        def location_to_tuple(location_dict):
            return tuple({k: v for k, v in location_dict.items() if k != 'query'}.items())

        return EventSummaryNumbers(
            persons_count=len(persons),
            workshops_accepted=len([r for r in registrations if not r.wait_listed
                                    and isinstance(self.tickets[r.ticket_key], WorkshopTicket)]),
            countries_count=len(set([p.location.get('country_code') for p in persons])),
            locations_count=len(set([location_to_tuple(p.location) for p in persons])),
        )


