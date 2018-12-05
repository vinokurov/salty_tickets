from dataclasses import dataclass
from salty_tickets.models.products import RegistrationProduct


@dataclass
class DiscountProduct(RegistrationProduct):
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
