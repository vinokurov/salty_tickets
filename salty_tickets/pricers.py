from typing import List, Dict

from dataclasses import dataclass, field
from salty_tickets.models.registrations import ProductRegistration


@dataclass
class ProductPricer:
    """
    A class to calculate prices for the selected products
    """
    event_products: dict = field(default_factory=dict)
    price_rules: list = field(default_factory=list)

    def __post_init__(self):
        if not self.price_rules:
            self.price_rules.append(BasePriceRule())

    def price_all(self, registrations: List[ProductRegistration]):
        for reg in registrations:
            reg.price = self.optimal_price(reg, registrations)

    def optimal_price(self, registration: ProductRegistration,
                      registration_list: List[ProductRegistration]) -> float:
        possible_prices = [rule.price(registration, registration_list, self.event_products)
                           for rule in self.price_rules]
        possible_prices = [p for p in possible_prices if p is not None]
        if possible_prices:
            price = min(possible_prices)
            return price

    @classmethod
    def from_event(cls, event):
        pricing_rules = [PRICING_RULES[k['name']](**k['kwargs']) for k in event.pricing_rules]
        return cls(event.products, pricing_rules)


class BasePriceRule:
    def price(self, registration, registration_list, event_products) -> float:
        return event_products[registration.product_key].base_price


@dataclass
class SpecialPriceIfMoreThanPriceRule(BasePriceRule):
    more_than: int
    special_price: float
    tag: str

    def price(self, registration, registration_list, event_products) -> float:
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


@dataclass
class CombinationsPriceRule(BasePriceRule):
    tag: str
    count_prices: Dict[int, float]

    def price(self, registration, registration_list, event_products) -> float:
        applicable_product_keys = [k for k, p in event_products.items()
                                   if self.tag in p.tags]
        if registration.product_key in applicable_product_keys:
            # make sure we count only purchase items for one person
            person = registration.person
            if person:
                counted_regs = [r for r in registration_list
                                if r.product_key in applicable_product_keys
                                and r.person == person]
                count = len(counted_regs)
                if str(count) in self.count_prices:
                    return self.count_prices[str(count)] / count


PRICING_RULES = {
    'special_price_if_more_than': SpecialPriceIfMoreThanPriceRule,
    'combination': CombinationsPriceRule,
}
