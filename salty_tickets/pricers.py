from typing import List, Dict

from dataclasses import dataclass, field
from salty_tickets.models.products import ProductRegistration, BaseProduct


@dataclass
class ProductPricer:
    """
    A class to calculate prices for the selected products
    """
    event_products: dict = field(default_factory=dict)
    price_rules: list = field(default_factory=list)

    def __post_init__(self):
        self.price_rules.append(BasePriceRule())

    def price(self, registrations: List[ProductRegistration]):
        for reg in registrations:
            reg.price = self.optimal_price(reg, registrations)

    def optimal_price(self, registration: ProductRegistration,
                      registration_list: List[ProductRegistration]):
        possible_prices = [rule.price(registration, registration_list, self.event_products)
                           for rule in self.price_rules]
        price = min([p for p in possible_prices if p is not None])
        return price

    @classmethod
    def from_event(cls, event):
        pricing_rules = [PRICING_RULES[k](**kwargs) for k, kwargs in event.pricing_rules.items()]
        return cls(event.products, pricing_rules)


class BasePriceRule:
    def price(self, registration, registration_list, event_products):
        return event_products[registration.product_key].base_price


@dataclass
class SpecialPriceIfMoreThanPriceRule(BasePriceRule):
    more_than: int
    special_price: float
    tag: str

    def price(self, registration, registration_list, event_products):
        applicable_product_keys = [k for k, p in event_products.items()
                                   if self.tag in p.tags]
        if registration.product_key in applicable_product_keys:
            already = [r for r in registration_list
                       if r.price is not None and r.product_key in applicable_product_keys]

            # make sure we count only purchase items for one person
            person = registration.person
            if person:
                already = [r for r in already if r.person == person]

            if len(already) >= self.more_than:
                return self.special_price


PRICING_RULES = {
    'special_price_if_more_than': SpecialPriceIfMoreThanPriceRule,
}
