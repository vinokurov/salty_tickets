from salty_tickets.models.personal_info import PersonInfo
from salty_tickets.models.products import BaseProduct, ProductRegistration
from salty_tickets.pricers import ProductPricer, SpecialPriceIfMoreThanPriceRule


def test_base_pricer():
    product_list = [
        BaseProduct(name='Product 1', base_price=10),
        BaseProduct(name='Product 2', base_price=20),
        BaseProduct(name='Product 3', base_price=30),
    ]

    event_products = {p.key: p for p in product_list}
    pricer = ProductPricer(event_products)

    registrations = [
        ProductRegistration(product_key=product_list[0].key),
        ProductRegistration(product_key=product_list[2].key),
    ]

    for r in registrations:
        assert r.price is None

    pricer.price(registrations)
    assert registrations[0].price == product_list[0].base_price
    assert registrations[1].price == product_list[2].base_price


def test_pricer_special_price_if_more_than():
    products = [
        BaseProduct(name='Product 1', base_price=25, tags={'offer'}),
        BaseProduct(name='Product 2', base_price=25, tags={'offer'}),
        BaseProduct(name='Product 3', base_price=25, tags={'offer'}),
        BaseProduct(name='Product 4', base_price=15, tags={'regular'}),
    ]

    event_products = {p.key: p for p in products}
    pricing_rules = [
        SpecialPriceIfMoreThanPriceRule(more_than=2, tag='offer', special_price=20)
    ]
    pricer = ProductPricer(event_products, pricing_rules)

    registrations = [ProductRegistration(product_key=p.key) for p in products]

    pricer.price(registrations)
    assert registrations[0].price == products[0].base_price
    assert registrations[1].price == products[1].base_price
    assert registrations[2].price == 20
    assert registrations[3].price == products[3].base_price


def test_pricer_special_price_if_more_than_2_persons():
    products = [
        BaseProduct(name='Product 1', base_price=25, tags={'offer'}),
        BaseProduct(name='Product 2', base_price=25, tags={'offer'}),
        BaseProduct(name='Product 3', base_price=25, tags={'offer'}),
        BaseProduct(name='Product 4', base_price=15, tags={'regular'}),
    ]

    event_products = {p.key: p for p in products}
    pricing_rules = [
        SpecialPriceIfMoreThanPriceRule(more_than=2, tag='offer', special_price=20)
    ]
    pricer = ProductPricer(event_products, pricing_rules)

    mr_one = PersonInfo(full_name='Mr One', email='Mr.One@one.com')
    ms_two = PersonInfo(full_name='Ms Two', email='Ms.Two@two.com')

    registrations = [
        ProductRegistration(product_key=products[0].key, person=mr_one),
        ProductRegistration(product_key=products[0].key, person=ms_two),

        ProductRegistration(product_key=products[1].key, person=mr_one),
        ProductRegistration(product_key=products[1].key, person=ms_two),

        ProductRegistration(product_key=products[2].key, person=ms_two),

        ProductRegistration(product_key=products[3].key, person=mr_one),
    ]

    pricer.price(registrations)
    assert [r.price for r in registrations] == [25, 25, 25, 25, 20, 15]
