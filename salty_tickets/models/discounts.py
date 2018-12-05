from dataclasses import dataclass
from salty_tickets.models.tickets import Ticket


@dataclass
class DiscountProduct(Ticket):
    pass


@dataclass
class GroupDiscount(DiscountProduct):
    pass


@dataclass
class OverseasDiscount(DiscountProduct):
    pass


@dataclass
class CodeDiscount(DiscountProduct):
    pass
