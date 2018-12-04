import pytest
from salty_tickets.models.registrations import PersonInfo, ProductRegistration
from salty_tickets.models.products import BaseProduct, WorkshopProduct, PartyProduct, FestivalPass
from salty_tickets.pricers import ProductPricer, SpecialPriceIfMoreThanPriceRule, CombinationsPriceRule, BasePriceRule, \
    MindTheShagPriceRule, TaggedBasePriceRule


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


@pytest.fixture
def mts_products():
    products = [
        WorkshopProduct(name='w1', base_price=35.0, tags={'station'}),
        WorkshopProduct(name='w2', base_price=35.0, tags={'station'}),
        WorkshopProduct(name='w3', base_price=35.0, tags={'station'}),
        WorkshopProduct(name='w4', base_price=35.0, tags={'station'}),
        WorkshopProduct(name='w5', base_price=35.0, tags={'station'}),
        WorkshopProduct(name='w6', base_price=35.0, tags={'station'}),
        WorkshopProduct(name='beg1', base_price=35.0, tags={'station', 'train'}),
        WorkshopProduct(name='beg2', base_price=35.0, tags={'station', 'train'}),
        WorkshopProduct(name='clinic', base_price=40.0, tags={'station', 'clinic'}),
        PartyProduct(name='p1', base_price=20.0, tags={'party'}),
        PartyProduct(name='p2', base_price=30.0, tags={'party'}),
        PartyProduct(name='p3', base_price=15.0, tags={'party'}),
        FestivalPass(name='full_weekend_ticket', base_price=120.0, tags={'pass'}),
        FestivalPass(name='full_weekend_ticket_no_parties', base_price=75.0, tags={'pass'}),
        FestivalPass(name='fast_shag_train', base_price=90.0, tags={'pass'}),
        FestivalPass(name='fast_shag_train_no_parties', base_price=45.0, tags={'pass'}),
        FestivalPass(name='party_pass', base_price=55.0, tags={'pass'}),
    ]
    return {p.key: p for p in products}


@pytest.fixture
def mts_pricing_rules():
    return [
        MindTheShagPriceRule(price_station=30.0, price_station_extra=25.0, price_clinic=40.0),
        TaggedBasePriceRule(tag='pass'),
        TaggedBasePriceRule(tag='party'),
    ]


@pytest.fixture
def mr_x():
    return PersonInfo(full_name='Mr.X', email='mr.x@x.com')


@pytest.fixture
def ms_y():
    return PersonInfo(full_name='Ms.Y', email='ms.y@y.com')


@pytest.mark.parametrize("registration_keys,expected_prices", [
    ("w1 w2", [30, 30]),
    ("p1 p2", [20, 30]),
    ("p3 beg1", [15, 30]),
    ("w1 w2 p3", [30, 30, 15]),
    ("w1 clinic p3", [30, 40, 15]),

    ('w1 w2 w3 p1 p2 p3 full_weekend_ticket', [0, 0, 0, 0, 0, 0, 120]),
    ('w1 w2 w3 full_weekend_ticket_no_parties', [0, 0, 0, 75]),
    ('w1 w2 w3 p1 p2 full_weekend_ticket_no_parties', [0, 0, 0, 20, 30, 75]),

    ('beg1 beg2 p1 p2 p3 fast_shag_train', [0, 0, 0, 0, 0, 90]),
    ('beg1 beg2 fast_shag_train_no_parties', [0, 0, 45]),
    ('beg1 beg2 p1 p2 fast_shag_train_no_parties', [0, 0, 20, 30, 45]),

    ('p1 p2 p3 party_pass', [0, 0, 0, 55]),
    ('w1 p1 p2 p3 party_pass', [30, 0, 0, 0, 55]),

    ('w1 w2 w3 w4 p1 p2 p3 full_weekend_ticket', [0, 0, 0, 25, 0, 0, 0, 120]),
    ('w1 w2 w3 w4 p2 p3 full_weekend_ticket_no_parties', [0, 0, 0, 25, 30, 15, 75]),

    ('w1 w2 w3 w4 w5 p1 p2 p3 full_weekend_ticket', [0, 0, 0, 25, 25, 0, 0, 0, 120]),
    ('w1 w2 w3 w4 w5 p2 p3 full_weekend_ticket_no_parties', [0, 0, 0, 25, 25, 30, 15, 75]),

    ('w1 beg1 beg2 p1 p2 p3 fast_shag_train', [25, 0, 0, 0, 0, 0, 90]),
    ('w1 beg1 beg2 p2 p3 fast_shag_train_no_parties', [25, 0, 0, 30, 15, 45]),

    ('w1 beg1 beg2 w2 p1 p2 p3 fast_shag_train', [25, 0, 0, 25, 0, 0, 0, 90]),
    ('w1 beg1 beg2 w2 p2 p3 fast_shag_train_no_parties', [25, 0, 0, 25, 30, 15, 45]),

    ('w1 w2 clinic p1 p2 p3 full_weekend_ticket', [0, 0, 15, 0, 0, 0, 120]),
    ('w1 w2 clinic full_weekend_ticket_no_parties', [0, 0, 15, 75]),

    ('w1 w2 clinic w3 p1 p2 p3 full_weekend_ticket', [0, 0, 15, 25, 0, 0, 0, 120]),
    ('w1 w2 clinic w3 full_weekend_ticket_no_parties', [0, 0, 15, 25, 75]),
    ('w1 w2 w3 clinic p1 p2 p3 full_weekend_ticket', [0, 0, 0, 40, 0, 0, 0, 120]),
    ('w1 w2 w3 clinic full_weekend_ticket_no_parties', [0, 0, 0, 40, 75]),
    ('w1 w2 w3 w4 clinic p1 p2 p3 full_weekend_ticket', [0, 0, 0, 25, 40, 0, 0, 0, 120]),
    ('w1 w2 w3 w4 clinic full_weekend_ticket_no_parties', [0, 0, 0, 25, 40, 75]),
])
def test_mind_the_shag_price_rule(mts_products, mts_pricing_rules, mr_x, ms_y, registration_keys, expected_prices):
    pricer = ProductPricer(mts_products, mts_pricing_rules)

    # solo registration
    registrations = [ProductRegistration(person=mr_x, registered_by=mr_x, product_key=k)
                     for k in registration_keys.split(' ')]
    pricer.price_all(registrations)
    assert sum(expected_prices) == sum([r.price for r in registrations])
    assert expected_prices == [r.price for r in registrations]

    # couple registration
    registrations_x = [ProductRegistration(person=mr_x, registered_by=mr_x, product_key=k)
                       for k in registration_keys.split(' ')]
    registrations_y = [ProductRegistration(person=ms_y, registered_by=mr_x, product_key=k)
                       for k in registration_keys.split(' ')]
    registrations_couple = registrations_x + registrations_y
    pricer.price_all(registrations_couple)
    expected_prices_couple = expected_prices + expected_prices
    assert sum(expected_prices_couple) == sum([r.price for r in registrations_couple])
    assert expected_prices_couple == [r.price for r in registrations_couple]

    # partner has just one workshop
    registrations_couple = registrations_x + [ProductRegistration(person=ms_y, registered_by=mr_x, product_key='w1')]
    pricer.price_all(registrations_couple)
    expected_prices_couple = expected_prices + [30]
    assert sum(expected_prices_couple) == sum([r.price for r in registrations_couple])
    assert expected_prices_couple == [r.price for r in registrations_couple]
