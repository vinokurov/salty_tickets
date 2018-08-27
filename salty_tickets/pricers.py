from dataclasses import dataclass, field


@dataclass
class ProductPricer:
    """
    A class to calculate prices for the selected products
    """
    event_products: dict = field(default_factory=dict)
    price_rules: list = field(default_factory=list)

    def __post_init__(self):
        self.price_rules.append(BasePriceRule())

    def price(self, purchase):
        for item in purchase.purchase_items:
            item.price = self.determine_product_price(item, purchase.purchase_items)

        purchase.update_total_price()

    def determine_product_price(self, item, purchase_items):
        possible_prices = [rule.price(item, purchase_items, self.event_products) for rule in self.price_rules]
        price = min([p for p in possible_prices if p is not None])
        return price


class BasePriceRule:
    def price(self, item, purchase_items, event_products):
        return event_products[item.product_key].base_price


@dataclass
class SpecialPriceIfMoreThanPriceRule(BasePriceRule):
    more_than: int
    special_price: float
    tag: str

    def price(self, item, purchase_items, event_products):
        applicable_product_keys = [k for k, p in event_products.items() if self.tag in p.tags]
        if item.product_key in applicable_product_keys:
            already = len([i for i in purchase_items if i.price is not None and i.product_key in applicable_product_keys])
            if already >= self.more_than:
                return self.special_price

