from salty_tickets.models.order import Purchase, PurchaseItem
from salty_tickets.models.products import BaseProduct
from salty_tickets.pricers import ProductPricer, SpecialPriceIfMoreThanPriceRule


def test_base_pricer():
    product_list = [
        BaseProduct(name='Product 1', base_price=10),
        BaseProduct(name='Product 2', base_price=20),
        BaseProduct(name='Product 3', base_price=30),
    ]

    event_products = {p.key: p for p in product_list}
    pricer = ProductPricer(event_products)

    purchase = Purchase(
        purchase_items=[
            PurchaseItem(name='Item 1', product_key=product_list[0].key),
            PurchaseItem(name='Item 3', product_key=product_list[2].key),
        ]
    )

    assert purchase.total_price == 0

    pricer.price(purchase)
    assert purchase.total_price == product_list[0].base_price + product_list[2].base_price
    assert purchase.purchase_items[0].price == product_list[0].base_price
    assert purchase.purchase_items[1].price == product_list[2].base_price


def test_pricer_special_price_if_more_than():
    product_list = [
        BaseProduct(name='Product 1', base_price=25, tags={'offer'}),
        BaseProduct(name='Product 2', base_price=25, tags={'offer'}),
        BaseProduct(name='Product 3', base_price=25, tags={'offer'}),
        BaseProduct(name='Product 4', base_price=15, tags={'regular'}),
    ]

    event_products = {p.key: p for p in product_list}
    pricing_rules = [
        SpecialPriceIfMoreThanPriceRule(more_than=2, tag='offer', special_price=20)
    ]
    pricer = ProductPricer(event_products, pricing_rules)

    purchase = Purchase(
        purchase_items=[PurchaseItem(name=f'Item - {p.name}', product_key=p.key) for p in product_list]
    )

    assert purchase.total_price == 0

    pricer.price(purchase)
    assert purchase.total_price == 25 + 25 + 20 + 15
    assert purchase.purchase_items[0].price == product_list[0].base_price
    assert purchase.purchase_items[1].price == product_list[1].base_price
    assert purchase.purchase_items[2].price == 20
    assert purchase.purchase_items[3].price == product_list[3].base_price
