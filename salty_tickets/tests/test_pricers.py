from salty_tickets.models.registrations import PersonInfo, ProductRegistration
from salty_tickets.models.products import BaseProduct
from salty_tickets.pricers import ProductPricer, SpecialPriceIfMoreThanPriceRule, CombinationsPriceRule, BasePriceRule


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

    pricer.price_all(registrations)
    assert registrations[0].price == product_list[0].base_price
    assert registrations[1].price == product_list[2].base_price


def test_pricer_special_price_if_more_than():
    products = [
        BaseProduct(name='Product 1', base_price=25, tags={'workshop'}),
        BaseProduct(name='Product 2', base_price=25, tags={'workshop'}),
        BaseProduct(name='Product 3', base_price=25, tags={'workshop'}),
        BaseProduct(name='Product 4', base_price=15, tags={'regular'}),
    ]

    event_products = {p.key: p for p in products}
    pricing_rules = [
        SpecialPriceIfMoreThanPriceRule(more_than=2, tag='workshop', special_price=20),
        BasePriceRule(),
    ]
    pricer = ProductPricer(event_products, pricing_rules)

    registrations = [ProductRegistration(product_key=p.key) for p in products]

    pricer.price_all(registrations)
    assert [25, 25, 20, 15] == [r.price for r in registrations]


def test_pricer_special_price_if_more_than_2_persons():
    products = [
        BaseProduct(name='Product 1', base_price=25, tags={'workshop'}),
        BaseProduct(name='Product 2', base_price=25, tags={'workshop'}),
        BaseProduct(name='Product 3', base_price=25, tags={'workshop'}),
        BaseProduct(name='Product 4', base_price=15, tags={'regular'}),
    ]

    event_products = {p.key: p for p in products}
    pricing_rules = [
        SpecialPriceIfMoreThanPriceRule(more_than=2, tag='workshop', special_price=20),
        BasePriceRule(),
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

    pricer.price_all(registrations)
    assert [r.price for r in registrations] == [25, 25, 25, 25, 20, 15]


def test_combinations_price_rule():
    products = [
        BaseProduct(name='w1', base_price=25, tags={'workshop'}),
        BaseProduct(name='w2', base_price=25, tags={'workshop'}),
        BaseProduct(name='w3', base_price=25, tags={'workshop'}),
        BaseProduct(name='p1', base_price=15, tags={'party'}),
        BaseProduct(name='p2', base_price=15, tags={'party'}),
    ]

    event_products = {p.key: p for p in products}
    pricing_rules = [
        CombinationsPriceRule(tag='workshop', count_prices={'2': 40, '3': 57}),
    ]
    pricer = ProductPricer(event_products, pricing_rules)

    mr_x = PersonInfo(full_name='Mr.X', email='mr.x@x.com')
    ms_y = PersonInfo(full_name='Ms.Y', email='ms.y@y.com')

    registrations = [
        ProductRegistration(person=mr_x, registered_by=mr_x, product_key='w1'),
        ProductRegistration(person=mr_x, registered_by=mr_x, product_key='w2'),
    ]
    pricer.price_all(registrations)
    assert [20.0, 20.0] == [r.price for r in registrations]

    registrations = [
        ProductRegistration(person=mr_x, registered_by=mr_x, product_key='w1'),
        ProductRegistration(person=mr_x, registered_by=mr_x, product_key='w2'),
        ProductRegistration(person=mr_x, registered_by=mr_x, product_key='w3'),
    ]
    pricer.price_all(registrations)
    assert [19, 19, 19] == [r.price for r in registrations]

    registrations = [
        ProductRegistration(person=mr_x, registered_by=mr_x, product_key='w1'),
        ProductRegistration(person=mr_x, registered_by=mr_x, product_key='w2'),
        ProductRegistration(person=ms_y, registered_by=mr_x, product_key='w1'),
    ]
    pricer.price_all(registrations)
    assert [20, 20, None] == [r.price for r in registrations]

    registrations = [
        ProductRegistration(person=mr_x, registered_by=mr_x, product_key='w1'),
        ProductRegistration(person=mr_x, registered_by=mr_x, product_key='w2'),
        ProductRegistration(person=mr_x, registered_by=mr_x, product_key='w3'),
        ProductRegistration(person=ms_y, registered_by=mr_x, product_key='w1'),
        ProductRegistration(person=ms_y, registered_by=mr_x, product_key='w2'),
    ]
    pricer.price_all(registrations)
    assert [19, 19, 19, 20, 20] == [r.price for r in registrations]
